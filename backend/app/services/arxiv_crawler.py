"""arXiv crawler service for automatic paper fetching and pushing."""
import os
import uuid
from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.arxiv import ArxivPaper, ArxivSubscription, ArxivPushRecord, ArxivCrawlLog
from app.models.paper import Paper
from app.services.arxiv_service import get_arxiv_service, ArxivService
from app.tasks.worker import (
    get_new_db,
    update_task_progress,
    complete_task,
    fail_task,
    create_task_record,
    launch_background_task,
)
from app.services.parsing_service import run_parsing_pipeline
from app.config import settings


def calculate_match_score(paper: ArxivPaper, subscription: ArxivSubscription) -> float:
    """Calculate matching score between paper and subscription (0-1)."""
    score = 0.0
    total_weight = 0.0

    # Keyword matching (weight: 0.6)
    if subscription.keywords:
        keyword_matches = 0
        keywords_lower = [kw.lower() for kw in subscription.keywords]
        title_lower = paper.title.lower()
        summary_lower = paper.summary.lower()

        for kw in keywords_lower:
            if kw in title_lower or kw in summary_lower:
                keyword_matches += 1

        keyword_score = keyword_matches / len(subscription.keywords)
        score += keyword_score * 0.6
        total_weight += 0.6

    # Category matching (weight: 0.3)
    if subscription.categories:
        paper_cats = set(paper.categories or [])
        sub_cats = set(subscription.categories)
        if paper_cats and sub_cats:
            intersection = paper_cats & sub_cats
            category_score = len(intersection) / len(sub_cats)
            score += category_score * 0.3
            total_weight += 0.3

    # Author matching (weight: 0.1)
    if subscription.authors:
        author_matches = 0
        paper_authors_lower = [a.lower() for a in (paper.authors or [])]

        for sub_author in subscription.authors:
            sub_author_lower = sub_author.lower()
            if any(sub_author_lower in pa for pa in paper_authors_lower):
                author_matches += 1

        author_score = author_matches / len(subscription.authors)
        score += author_score * 0.1
        total_weight += 0.1

    # Normalize if not all criteria are used
    if total_weight > 0:
        score = score / total_weight

    return min(score, 1.0)


def run_arxiv_crawl(subscription_id: str, task_id: str):
    """Background task to crawl arXiv for a subscription."""
    db = get_new_db()
    try:
        # Create crawl log
        crawl_log = ArxivCrawlLog(
            id=str(uuid.uuid4()),
            subscription_id=subscription_id,
            status="running",
            started_at=datetime.now(timezone.utc),
        )
        db.add(crawl_log)
        db.commit()

        # Get subscription
        update_task_progress(db, task_id, 0.1, "Fetching subscription...")
        subscription = db.query(ArxivSubscription).get(subscription_id)
        if not subscription:
            raise ValueError(f"Subscription {subscription_id} not found")

        # Build query
        update_task_progress(db, task_id, 0.2, "Building search query...")
        arxiv = get_arxiv_service()

        query_parts = []
        if subscription.keywords:
            keyword_query = " AND ".join(f'all:"{kw}"' for kw in subscription.keywords)
            query_parts.append(f"({keyword_query})")

        if subscription.categories:
            cat_query = " OR ".join(f"cat:{cat}" for cat in subscription.categories)
            query_parts.append(f"({cat_query})")

        if subscription.authors:
            author_query = " OR ".join(f'au:"{author}"' for author in subscription.authors)
            query_parts.append(f"({author_query})")

        query = " AND ".join(query_parts) if query_parts else "all:*"

        # Add date filter if last_crawled exists
        if subscription.last_crawled:
            date_str = subscription.last_crawled.strftime("%Y%m%d")
            query += f" AND submittedDate:[{date_str} TO *]"

        # Fetch papers
        update_task_progress(db, task_id, 0.3, "Querying arXiv API...")
        papers = arxiv.search_papers(
            query=query,
            max_results=subscription.max_results,
            sort_by="submittedDate",
            sort_order="descending",
        )

        update_task_progress(db, task_id, 0.5, f"Processing {len(papers)} papers...")

        # Process papers
        new_count = 0
        pushed_count = 0

        for i, paper in enumerate(papers):
            progress = 0.5 + (0.4 * (i + 1) / len(papers))
            update_task_progress(db, task_id, progress, f"Processing paper {i+1}/{len(papers)}...")

            # Check if paper already exists
            existing = db.query(ArxivPaper).filter(ArxivPaper.id == paper.id).first()
            is_new = False

            if not existing:
                db.add(paper)
                new_count += 1
                is_new = True

            # Check if push record already exists
            existing_push = db.query(ArxivPushRecord).filter(
                ArxivPushRecord.user_id == subscription.user_id,
                ArxivPushRecord.arxiv_paper_id == paper.id,
                ArxivPushRecord.subscription_id == subscription.id,
            ).first()

            if not existing_push:
                # Calculate match score
                score = calculate_match_score(paper, subscription)

                # Only push if score is above threshold (0.3)
                if score >= 0.3:
                    push_record = ArxivPushRecord(
                        id=str(uuid.uuid4()),
                        user_id=subscription.user_id,
                        subscription_id=subscription.id,
                        arxiv_paper_id=paper.id,
                        match_score=score,
                        is_read=False,
                        is_imported=False,
                    )
                    db.add(push_record)
                    pushed_count += 1

        # Update subscription last_crawled
        subscription.last_crawled = datetime.now(timezone.utc)

        # Update crawl log
        crawl_log.status = "completed"
        crawl_log.papers_found = len(papers)
        crawl_log.papers_new = new_count
        crawl_log.papers_pushed = pushed_count
        crawl_log.completed_at = datetime.now(timezone.utc)

        db.commit()

        update_task_progress(db, task_id, 1.0, f"Found {new_count} new papers, pushed {pushed_count}")
        complete_task(db, task_id, {"new_papers": new_count, "pushed": pushed_count})

    except Exception as e:
        db.rollback()

        # Update crawl log with error
        if 'crawl_log' in locals():
            crawl_log.status = "failed"
            crawl_log.error_message = str(e)
            crawl_log.completed_at = datetime.now(timezone.utc)
            db.commit()

        fail_task(db, task_id, str(e))
        import traceback
        traceback.print_exc()

    finally:
        db.close()


def import_arxiv_paper_to_local(db: Session, arxiv_id: str, user_id: str) -> Paper:
    """Import an arXiv paper to local library."""
    # Get arXiv paper info
    arxiv_paper = db.query(ArxivPaper).filter(ArxivPaper.id == arxiv_id).first()

    if not arxiv_paper:
        # Fetch from arXiv if not in cache
        arxiv = get_arxiv_service()
        papers = arxiv.search_papers(f"id:{arxiv_id}", max_results=1)
        if not papers:
            raise ValueError(f"Paper {arxiv_id} not found on arXiv")
        arxiv_paper = papers[0]
        db.add(arxiv_paper)
        db.commit()

    # Create uploads/arxiv directory if not exists
    arxiv_upload_dir = os.path.join(settings.upload_dir, "arxiv")
    os.makedirs(arxiv_upload_dir, exist_ok=True)

    # Download PDF
    pdf_filename = f"{arxiv_id}.pdf"
    pdf_path = os.path.join(arxiv_upload_dir, pdf_filename)

    if not os.path.exists(pdf_path):
        arxiv = get_arxiv_service()
        success = arxiv.download_pdf(arxiv_id, arxiv_paper.pdf_url, pdf_path)
        if not success:
            raise ValueError(f"Failed to download PDF for {arxiv_id}")

    # Get file size
    file_size = os.path.getsize(pdf_path)

    # Create Paper record
    paper = Paper(
        id=str(uuid.uuid4()),
        title=arxiv_paper.title,
        authors=arxiv_paper.authors or [],
        abstract=arxiv_paper.summary or "",
        pdf_path=pdf_path,
        file_size=file_size,
        parsing_status="pending",
        language="unknown",  # Will be detected during parsing
    )
    db.add(paper)
    db.commit()
    db.refresh(paper)

    # Update push record if exists
    push_record = db.query(ArxivPushRecord).filter(
        ArxivPushRecord.arxiv_paper_id == arxiv_id,
        ArxivPushRecord.user_id == user_id,
    ).first()

    if push_record:
        push_record.is_imported = True
        push_record.imported_paper_id = paper.id
        db.commit()

    # Trigger parsing task
    task = create_task_record(db, paper.id, "parsing")
    launch_background_task(
        task.id,
        run_parsing_pipeline,
        paper.id,
        task.id,
    )

    return paper


def crawl_all_subscriptions():
    """Crawl arXiv for all active subscriptions."""
    db = get_new_db()
    try:
        subscriptions = db.query(ArxivSubscription).filter(
            ArxivSubscription.is_active == True
        ).all()

        for subscription in subscriptions:
            task = create_task_record(db, None, "arxiv_crawl")
            launch_background_task(
                task.id,
                run_arxiv_crawl,
                subscription.id,
                task.id,
            )

        return len(subscriptions)

    finally:
        db.close()
