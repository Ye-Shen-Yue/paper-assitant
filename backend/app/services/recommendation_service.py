"""Recommendation service for personalized paper recommendations and user profiling."""
import uuid
import json
from typing import List, Dict, Optional
from collections import Counter
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from app.models.recommendation import UserActivity, PaperEmbedding, UserProfile, RecommendationLog
from app.models.paper import Paper
from app.core.llm.client import LLMClient


class RecommendationService:
    """Service for generating recommendations and user profiles."""

    def __init__(self, db: Session):
        self.db = db
        self.llm = LLMClient()

    # ========== Paper Embedding ==========

    def generate_paper_embedding(self, paper: Paper) -> Optional[List[float]]:
        """Generate vector embedding for a paper using LLM."""
        try:
            # Extract keywords first
            keywords = self._extract_keywords(paper)

            # Create text representation
            text_repr = f"{paper.title} [SEP] {paper.abstract or ''} [SEP] {', '.join(keywords)}"

            # Generate embedding using OpenAI
            import openai
            from app.config import settings

            client = openai.OpenAI(
                api_key=settings.llm_api_key or settings.qwen_api_key,
                base_url=settings.llm_base_url if settings.llm_api_key else settings.qwen_base_url,
            )

            response = client.embeddings.create(
                model="text-embedding-3-small",
                input=text_repr[:8000],  # Limit input length
            )

            embedding = response.data[0].embedding

            # Store in database
            paper_emb = self.db.query(PaperEmbedding).filter(PaperEmbedding.paper_id == paper.id).first()
            if paper_emb:
                paper_emb.embedding = embedding
                paper_emb.keywords = keywords
                paper_emb.updated_at = datetime.now(timezone.utc)
            else:
                paper_emb = PaperEmbedding(
                    id=str(uuid.uuid4()),
                    paper_id=paper.id,
                    embedding=embedding,
                    keywords=keywords,
                    topics=self._classify_topics(keywords),
                )
                self.db.add(paper_emb)

            self.db.commit()
            return embedding

        except Exception as e:
            print(f"Failed to generate embedding for paper {paper.id}: {e}")
            return None

    def _extract_keywords(self, paper: Paper) -> List[str]:
        """Extract keywords from paper using LLM."""
        try:
            prompt = f"""Extract 5-10 key technical keywords from this research paper. Return only a JSON array of strings.

Title: {paper.title}
Abstract: {paper.abstract or 'N/A'}

Example output: ["Transformer", "Attention Mechanism", "Large Language Model", "Fine-tuning"]
"""
            response = self.llm.chat(
                prompt=prompt,
                system_prompt="You are a research paper analysis assistant. Extract technical keywords.",
                temperature=0.3,
            )

            # Parse JSON from response
            import re
            json_match = re.search(r'\[.*?\]', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return []
        except Exception as e:
            print(f"Keyword extraction failed: {e}")
            return []

    def _classify_topics(self, keywords: List[str]) -> List[str]:
        """Classify keywords into research topics."""
        topic_mapping = {
            "NLP": ["nlp", "natural language", "transformer", "bert", "gpt", "llm", "language model",
                   "tokenization", "embedding", "sentiment", "translation", "summarization"],
            "CV": ["cv", "computer vision", "image", "cnn", "resnet", "yolo", "object detection",
                  "segmentation", "classification", "gan", "diffusion"],
            "ML": ["ml", "machine learning", "deep learning", "neural network", "training",
                  "optimization", "gradient", "loss function", "regularization"],
            "Robotics": ["robot", "robotics", "control", "manipulation", "navigation", "slam"],
            "Data Mining": ["data mining", "knowledge discovery", "clustering", "association"],
            "Graph": ["graph", "gnn", "graph neural", "network", "node", "edge"],
            "Reinforcement Learning": ["rl", "reinforcement", "q-learning", "policy", "agent", "reward"],
        }

        topics = set()
        for keyword in keywords:
            keyword_lower = keyword.lower()
            for topic, indicators in topic_mapping.items():
                if any(ind in keyword_lower for ind in indicators):
                    topics.add(topic)

        return list(topics)

    # ========== User Profile ==========

    def update_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """Update user profile based on activity history."""
        try:
            # Get recent activities (last 90 days)
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=90)
            activities = (
                self.db.query(UserActivity)
                .filter(UserActivity.user_id == user_id)
                .filter(UserActivity.created_at >= cutoff_date)
                .all()
            )

            if not activities:
                return None

            # Calculate metrics
            total_papers = len(set(a.paper_id for a in activities if a.activity_type == 'view'))
            total_time = sum(a.duration_seconds for a in activities if a.activity_type == 'view')

            # Calculate streak
            streak_days = self._calculate_streak(user_id)

            # Get recent paper IDs
            recent_papers = (
                self.db.query(UserActivity.paper_id)
                .filter(UserActivity.user_id == user_id)
                .filter(UserActivity.activity_type == 'view')
                .order_by(UserActivity.created_at.desc())
                .limit(20)
                .distinct()
                .all()
            )
            last_read_papers = [p[0] for p in recent_papers]

            # Calculate topic distribution
            topic_counts = Counter()
            for activity in activities:
                if activity.activity_type == 'view' and activity.duration_seconds > 30:
                    emb = self.db.query(PaperEmbedding).filter(
                        PaperEmbedding.paper_id == activity.paper_id
                    ).first()
                    if emb and emb.topics:
                        for topic in emb.topics:
                            topic_counts[topic] += 1

            # Normalize topic distribution
            total_topics = sum(topic_counts.values())
            topic_distribution = {
                k: round(v / total_topics, 3) for k, v in topic_counts.items()
            } if total_topics > 0 else {}

            # Get method preferences from keywords
            all_keywords = []
            for activity in activities:
                if activity.activity_type == 'view':
                    emb = self.db.query(PaperEmbedding).filter(
                        PaperEmbedding.paper_id == activity.paper_id
                    ).first()
                    if emb and emb.keywords:
                        all_keywords.extend(emb.keywords)

            method_preferences = [kw for kw, _ in Counter(all_keywords).most_common(10)]

            # Determine reading pattern
            avg_duration = total_time / total_papers if total_papers > 0 else 0
            reading_pattern = "researcher" if avg_duration > 600 else "browser"  # 10 min threshold

            # Calculate profile embedding
            profile_embedding = self._calculate_profile_embedding(user_id, activities)

            # Update or create profile
            profile = self.db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
            if profile:
                profile.topic_distribution = topic_distribution
                profile.method_preferences = method_preferences
                profile.profile_embedding = profile_embedding
                profile.reading_pattern = reading_pattern
                profile.total_papers_read = total_papers
                profile.total_reading_time = total_time
                profile.streak_days = streak_days
                profile.last_read_papers = last_read_papers
                profile.updated_at = datetime.now(timezone.utc)
            else:
                profile = UserProfile(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    topic_distribution=topic_distribution,
                    method_preferences=method_preferences,
                    profile_embedding=profile_embedding,
                    reading_pattern=reading_pattern,
                    total_papers_read=total_papers,
                    total_reading_time=total_time,
                    streak_days=streak_days,
                    last_read_papers=last_read_papers,
                )
                self.db.add(profile)

            self.db.commit()
            return profile

        except Exception as e:
            print(f"Failed to update user profile: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _calculate_streak(self, user_id: str) -> int:
        """Calculate consecutive reading days."""
        activities = (
            self.db.query(UserActivity)
            .filter(UserActivity.user_id == user_id)
            .filter(UserActivity.activity_type == 'view')
            .order_by(UserActivity.created_at.desc())
            .all()
        )

        if not activities:
            return 0

        # Get unique dates
        dates = set()
        for a in activities:
            date = a.created_at.date()
            dates.add(date)

        # Calculate streak
        sorted_dates = sorted(dates, reverse=True)
        today = datetime.now(timezone.utc).date()

        streak = 0
        check_date = today

        for date in sorted_dates:
            if date == check_date or date == today:
                streak += 1
                check_date = date - timedelta(days=1)
            elif date == check_date:
                streak += 1
                check_date = date - timedelta(days=1)
            else:
                break

        return streak

    def _calculate_profile_embedding(self, user_id: str, activities: List[UserActivity]) -> List[float]:
        """Calculate user profile as weighted average of paper embeddings."""
        embeddings = []
        weights = []

        for activity in activities:
            if activity.activity_type != 'view':
                continue

            emb_record = self.db.query(PaperEmbedding).filter(
                PaperEmbedding.paper_id == activity.paper_id
            ).first()

            if emb_record and emb_record.embedding:
                embeddings.append(emb_record.embedding)
                # Weight by reading time (normalize to minutes)
                weight = max(activity.duration_seconds / 60, 1)
                weights.append(weight)

        if not embeddings:
            return []

        # Calculate weighted average
        embeddings_array = np.array(embeddings)
        weights_array = np.array(weights)
        weights_array = weights_array / weights_array.sum()

        profile_emb = np.average(embeddings_array, axis=0, weights=weights_array)
        return profile_emb.tolist()

    # ========== Recommendation Generation ==========

    def generate_recommendations(
        self,
        user_id: str,
        limit: int = 10,
        rec_type: str = "mixed"
    ) -> List[Dict]:
        """Generate personalized paper recommendations."""
        try:
            # Get user profile
            profile = self.db.query(UserProfile).filter(UserProfile.user_id == user_id).first()

            # Get content-based scores
            content_scores = {}
            if rec_type in ["mixed", "content"]:
                content_scores = self._content_based_scores(user_id, profile)

            # Get trending scores
            trending_scores = {}
            if rec_type in ["mixed", "trending"]:
                trending_scores = self._trending_scores()

            # Combine scores
            final_scores = {}
            all_paper_ids = set(content_scores.keys()) | set(trending_scores.keys())

            for paper_id in all_paper_ids:
                if rec_type == "content":
                    score = content_scores.get(paper_id, 0)
                elif rec_type == "trending":
                    score = trending_scores.get(paper_id, 0)
                else:  # mixed
                    score = (
                        0.7 * content_scores.get(paper_id, 0) +
                        0.3 * trending_scores.get(paper_id, 0)
                    )
                final_scores[paper_id] = score

            # Sort and get top N
            sorted_papers = sorted(final_scores.items(), key=lambda x: x[1], reverse=True)

            # Build response
            recommendations = []
            for paper_id, score in sorted_papers[:limit]:
                paper = self.db.query(Paper).filter(Paper.id == paper_id).first()
                if not paper:
                    continue

                # Determine reason
                if paper_id in content_scores and content_scores.get(paper_id, 0) > 0.7:
                    reason = "content_based"
                    reason_text = self._generate_reason_text(paper, profile)
                else:
                    reason = "trending"
                    reason_text = "近期热门论文"

                from app.schemas.paper import PaperSummary
                recommendations.append({
                    "paper": PaperSummary.model_validate(paper),
                    "reason": reason,
                    "reason_text": reason_text,
                    "score": round(score, 3),
                })

            return recommendations

        except Exception as e:
            print(f"Recommendation generation failed: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _content_based_scores(self, user_id: str, profile: Optional[UserProfile]) -> Dict[str, float]:
        """Calculate content-based similarity scores."""
        scores = {}

        if not profile or not profile.profile_embedding:
            return scores

        user_emb = np.array(profile.profile_embedding).reshape(1, -1)

        # Get recent papers (last 30 days)
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)

        # Get papers user hasn't read
        read_papers = (
            self.db.query(UserActivity.paper_id)
            .filter(UserActivity.user_id == user_id)
            .filter(UserActivity.activity_type == 'view')
            .distinct()
            .all()
        )
        read_paper_ids = {p[0] for p in read_papers}

        # Get candidate papers with embeddings
        candidates = (
            self.db.query(Paper, PaperEmbedding)
            .join(PaperEmbedding, Paper.id == PaperEmbedding.paper_id)
            .filter(Paper.upload_date >= cutoff_date)
            .filter(~Paper.id.in_(read_paper_ids) if read_paper_ids else True)
            .all()
        )

        for paper, emb in candidates:
            if not emb.embedding:
                continue

            paper_emb = np.array(emb.embedding).reshape(1, -1)
            similarity = cosine_similarity(user_emb, paper_emb)[0][0]

            # Boost score for papers with matching topics
            if profile.topic_distribution and emb.topics:
                topic_boost = 0
                for topic in emb.topics:
                    if topic in profile.topic_distribution:
                        topic_boost += profile.topic_distribution[topic] * 0.1
                similarity += topic_boost

            scores[paper.id] = float(similarity)

        return scores

    def _trending_scores(self) -> Dict[str, float]:
        """Calculate trending scores based on recent views."""
        # Get view counts for recent papers
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=7)

        trending = (
            self.db.query(UserActivity.paper_id)
            .filter(UserActivity.activity_type == 'view')
            .filter(UserActivity.created_at >= cutoff_date)
            .all()
        )

        paper_counts = Counter(p[0] for p in trending)

        # Normalize to 0-1 range
        if not paper_counts:
            return {}

        max_count = max(paper_counts.values())
        return {paper_id: count / max_count for paper_id, count in paper_counts.items()}

    def _generate_reason_text(self, paper: Paper, profile: Optional[UserProfile]) -> str:
        """Generate human-readable recommendation reason."""
        if not profile:
            return "基于你的阅读兴趣"

        # Get paper embedding info
        emb = self.db.query(PaperEmbedding).filter(
            PaperEmbedding.paper_id == paper.id
        ).first()

        if emb and emb.topics:
            # Find matching topics
            matching_topics = []
            for topic in emb.topics:
                if profile.topic_distribution and topic in profile.topic_distribution:
                    matching_topics.append(topic)

            if matching_topics:
                topics_str = "、".join(matching_topics[:2])
                return f"与你关注的[{topics_str}]领域相关"

        return "基于你的阅读历史推荐"

    # ========== Trend Analysis ==========

    def get_trend_data(
        self,
        user_id: str,
        topics: Optional[List[str]],
        years: int = 10
    ) -> Dict:
        """Get trend data for visualization."""
        try:
            cutoff_year = datetime.now(timezone.utc).year - years

            # Get all paper embeddings with topics
            embeddings = self.db.query(PaperEmbedding).all()

            # Filter by topics if specified
            if topics:
                embeddings = [e for e in embeddings if any(t in (e.topics or []) for t in topics)]

            # Build heatmap data
            topic_yearly_counts = {}
            for emb in embeddings:
                paper = self.db.query(Paper).filter(Paper.id == emb.paper_id).first()
                if not paper or not paper.upload_date:
                    continue

                year = paper.upload_date.year if hasattr(paper.upload_date, 'year') else datetime.now(timezone.utc).year

                if year < cutoff_year:
                    continue

                for topic in (emb.topics or []):
                    if topic not in topic_yearly_counts:
                        topic_yearly_counts[topic] = {}
                    if year not in topic_yearly_counts[topic]:
                        topic_yearly_counts[topic][year] = 0
                    topic_yearly_counts[topic][year] += 1

            # Format heatmap data
            heatmap_data = []
            for topic, yearly_data in topic_yearly_counts.items():
                for year, count in yearly_data.items():
                    heatmap_data.append({
                        "topic": topic,
                        "year": year,
                        "count": count,
                    })

            # Get keyword evolution
            keyword_evolution = self._get_keyword_evolution(embeddings, years)

            # Get emerging topics
            emerging_topics = self._get_emerging_topics(embeddings)

            # Generate AI summary
            ai_summary = self._generate_trend_summary(topic_yearly_counts, emerging_topics)

            return {
                "heatmap_data": heatmap_data,
                "keyword_evolution": keyword_evolution,
                "emerging_topics": emerging_topics,
                "ai_summary": ai_summary,
            }

        except Exception as e:
            print(f"Trend data generation failed: {e}")
            import traceback
            traceback.print_exc()
            return {
                "heatmap_data": [],
                "keyword_evolution": [],
                "emerging_topics": [],
                "ai_summary": "暂无趋势数据",
            }

    def _get_keyword_evolution(self, embeddings: List[PaperEmbedding], years: int) -> List[Dict]:
        """Track keyword popularity over time."""
        cutoff_year = datetime.now(timezone.utc).year - years

        keyword_yearly = {}
        for emb in embeddings:
            paper = self.db.query(Paper).filter(Paper.id == emb.paper_id).first()
            if not paper or not paper.upload_date:
                continue

            year = paper.upload_date.year if hasattr(paper.upload_date, 'year') else datetime.now(timezone.utc).year

            if year < cutoff_year:
                continue

            for keyword in (emb.keywords or [])[:5]:  # Top 5 keywords
                if keyword not in keyword_yearly:
                    keyword_yearly[keyword] = {}
                if year not in keyword_yearly[keyword]:
                    keyword_yearly[keyword][year] = 0
                keyword_yearly[keyword][year] += 1

        # Format for chart
        evolution_data = []
        for keyword, yearly in keyword_yearly.items():
            evolution_data.append({
                "keyword": keyword,
                "data": [{"year": y, "count": c} for y, c in sorted(yearly.items())],
            })

        # Sort by total count and take top 10
        evolution_data.sort(key=lambda x: sum(d["count"] for d in x["data"]), reverse=True)
        return evolution_data[:10]

    def _get_emerging_topics(self, embeddings: List[PaperEmbedding]) -> List[Dict]:
        """Identify emerging topics based on recent growth."""
        current_year = datetime.now(timezone.utc).year

        # Count by time periods
        recent_counts = Counter()
        older_counts = Counter()

        for emb in embeddings:
            paper = self.db.query(Paper).filter(Paper.id == emb.paper_id).first()
            if not paper or not paper.upload_date:
                continue

            year = paper.upload_date.year if hasattr(paper.upload_date, 'year') else current_year

            for keyword in (emb.keywords or []):
                if year >= current_year - 1:  # Recent 2 years
                    recent_counts[keyword] += 1
                elif year >= current_year - 3:  # 3-4 years ago
                    older_counts[keyword] += 1

        # Calculate growth rate
        emerging = []
        for keyword, recent in recent_counts.items():
            older = older_counts.get(keyword, 1)  # Avoid division by zero
            if older > 0:
                growth = ((recent - older) / older) * 100
                if growth > 50:  # More than 50% growth
                    emerging.append({
                        "topic": keyword,
                        "growth_rate": round(growth, 1),
                        "recent_count": recent,
                    })

        # Sort by growth rate
        emerging.sort(key=lambda x: x["growth_rate"], reverse=True)
        return emerging[:10]

    def _generate_trend_summary(self, topic_yearly_counts: Dict, emerging_topics: List[Dict]) -> str:
        """Generate AI summary of trends."""
        try:
            # Build prompt
            topic_summary = "\n".join([
                f"- {topic}: {sum(yearly.values())} papers over {len(yearly)} years"
                for topic, yearly in list(topic_yearly_counts.items())[:5]
            ])

            emerging_str = "\n".join([
                f"- {t['topic']}: +{t['growth_rate']}% growth"
                for t in emerging_topics[:5]
            ])

            prompt = f"""Based on the following research trend data, generate a concise summary (2-3 sentences) in Chinese:

Main research areas:
{topic_summary}

Emerging hot topics:
{emerging_str}

Provide insights on the overall trend and suggest what researchers should pay attention to."""

            summary = self.llm.chat(
                prompt=prompt,
                system_prompt="You are a research trend analyst. Summarize trends concisely.",
                temperature=0.5,
                max_tokens=200,
            )

            return summary.strip()

        except Exception as e:
            print(f"Trend summary generation failed: {e}")
            return "研究趋势分析正在完善中..."
