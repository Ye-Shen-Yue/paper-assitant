import type { PaperDetail } from '../../api/types';
import { useState, useEffect } from 'react';
import { SECTION_TYPE_KEYS, ENTITY_TYPE_COLORS, ENTITY_TYPE_KEYS } from '../../utils/constants';
import { useT } from '../../hooks/useTranslation';
import { generateTables, type GeneratedTable } from '../../api/tables';

interface Props {
  paper: PaperDetail;
}

export default function OverviewTab({ paper }: Props) {
  const t = useT();
  const [generatedTables, setGeneratedTables] = useState<GeneratedTable[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGenerateTables = async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await generateTables(paper.id);
      setGeneratedTables(result.tables);
    } catch (err) {
      console.error('Failed to generate tables:', err);
      setError('Failed to generate tables. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Abstract */}
      {paper.abstract && (
        <section className="bg-white rounded-lg border border-slate-200 p-5">
          <h3 className="text-sm font-semibold text-slate-700 mb-3">{t('overview.abstract')}</h3>
          <p className="text-sm text-slate-600 leading-relaxed">{paper.abstract}</p>
        </section>
      )}

      {/* Keywords */}
      {paper.keywords.length > 0 && (
        <section className="bg-white rounded-lg border border-slate-200 p-5">
          <h3 className="text-sm font-semibold text-slate-700 mb-3">{t('overview.keywords')}</h3>
          <div className="flex flex-wrap gap-2">
            {paper.keywords.map((kw, i) => (
              <span key={i} className="px-2 py-1 bg-blue-50 text-blue-700 text-xs rounded-md">
                {kw}
              </span>
            ))}
          </div>
        </section>
      )}

      {/* Sections */}
      {paper.sections.length > 0 && (
        <section className="bg-white rounded-lg border border-slate-200 p-5">
          <h3 className="text-sm font-semibold text-slate-700 mb-3">
            {t('overview.sections')} ({paper.sections.length})
          </h3>
          <div className="space-y-4">
            {paper.sections
              .filter((s) => s.section_type !== 'title')
              .map((section) => (
                <div key={section.id} className="border-l-2 border-blue-200 pl-4">
                  <h4 className="text-sm font-medium text-slate-700">
                    <span className="text-xs text-blue-500 mr-2">
                      [{SECTION_TYPE_KEYS[section.section_type] ? t(SECTION_TYPE_KEYS[section.section_type]) : section.section_type}]
                    </span>
                    {section.heading}
                  </h4>
                  <p className="text-xs text-slate-500 mt-1 line-clamp-3">
                    {section.content.slice(0, 300)}
                    {section.content.length > 300 ? '...' : ''}
                  </p>
                </div>
              ))}
          </div>
        </section>
      )}

      {/* Entities */}
      {paper.entities.length > 0 && (
        <section className="bg-white rounded-lg border border-slate-200 p-5">
          <h3 className="text-sm font-semibold text-slate-700 mb-3">
            {t('overview.entities')} ({paper.entities.length})
          </h3>
          <div className="flex flex-wrap gap-2">
            {paper.entities.map((ent) => (
              <span
                key={ent.id}
                className="px-2 py-1 text-xs rounded-md text-white"
                style={{ backgroundColor: ENTITY_TYPE_COLORS[ent.entity_type] || '#6b7280' }}
                title={`${ENTITY_TYPE_KEYS[ent.entity_type] ? t(ENTITY_TYPE_KEYS[ent.entity_type]) : ent.entity_type} (${(ent.confidence * 100).toFixed(0)}%)`}
              >
                {ent.text}
              </span>
            ))}
          </div>
          {/* Legend */}
          <div className="flex flex-wrap gap-3 mt-4 pt-3 border-t border-slate-100">
            {Object.entries(ENTITY_TYPE_KEYS).map(([type, key]) => (
              <span key={type} className="flex items-center gap-1 text-xs text-slate-500">
                <span
                  className="w-2.5 h-2.5 rounded-full"
                  style={{ backgroundColor: ENTITY_TYPE_COLORS[type] }}
                />
                {t(key)}
              </span>
            ))}
          </div>
        </section>
      )}

      {/* Kimi Generated Tables */}
      <section className="bg-white rounded-lg border border-slate-200">
        <div className="px-5 py-4 border-b border-slate-200 bg-slate-50/50 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-slate-800">
            AI-Generated Tables
            {generatedTables && (
              <span className="ml-2 text-xs font-normal text-slate-500">({generatedTables.length} tables)</span>
            )}
          </h3>
          <button
            onClick={handleGenerateTables}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {loading ? (
              <>
                <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Generating...
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
                </svg>
                Generate Tables with Kimi
              </>
            )}
          </button>
        </div>

        <div className="p-5">
          {error && (
            <div className="text-sm text-red-600 mb-4">{error}</div>
          )}

          {!generatedTables && !loading && !error && (
            <div className="text-center py-12 text-slate-400">
              <svg className="w-12 h-12 mx-auto mb-3 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
              <p className="text-sm">Click "Generate Tables with Kimi" to extract key information into LaTeX tables</p>
            </div>
          )}

          {generatedTables && generatedTables.length === 0 && (
            <div className="text-center py-12 text-slate-400">
              <p className="text-sm">No tables could be generated from this paper.</p>
            </div>
          )}

          {generatedTables && generatedTables.length > 0 && (
            <div className="space-y-8">
              {generatedTables.map((table, idx) => (
                <div key={idx} className="border border-slate-200 rounded-lg overflow-hidden">
                  {/* Table Title */}
                  <div className="px-4 py-3 bg-slate-100 border-b border-slate-200">
                    <h4 className="text-sm font-semibold text-slate-800">{table.table_title}</h4>
                  </div>

                  {/* Two Column Layout */}
                  <div className="grid grid-cols-1 lg:grid-cols-2 divide-y lg:divide-y-0 lg:divide-x divide-slate-200">
                    {/* Left: LaTeX Table */}
                    <div className="p-4">
                      <div className="text-xs font-semibold text-slate-500 mb-2 uppercase tracking-wide">LaTeX Table</div>
                      <LatexTable latex={table.latex_code} />
                    </div>

                    {/* Right: Explanation */}
                    <div className="p-4 bg-blue-50/30">
                      <div className="text-xs font-semibold text-blue-600 mb-2 uppercase tracking-wide flex items-center gap-1">
                        <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                        </svg>
                        Kimi Explanation
                      </div>
                      <div className="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">
                        {table.explanation}
                      </div>
                    </div>
                  </div>

                  {/* LaTeX Code Toggle */}
                  <details className="border-t border-slate-200">
                    <summary className="px-4 py-2 text-xs text-slate-500 cursor-pointer hover:bg-slate-50 select-none">
                      View LaTeX Source Code
                    </summary>
                    <pre className="px-4 py-3 bg-slate-900 text-slate-300 text-xs overflow-x-auto">
                      <code>{table.latex_code}</code>
                    </pre>
                  </details>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>
    </div>
  );
}

// Sub-component: Render LaTeX table as HTML
function LatexTable({ latex }: { latex: string }) {
  const tableData = parseLatexTable(latex);

  if (!tableData) {
    return <pre className="text-xs text-slate-600 overflow-x-auto">{latex}</pre>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm border-collapse">
        <thead>
          <tr className="border-b-2 border-slate-800">
            {tableData.headers.map((h, i) => (
              <th
                key={i}
                className={`px-3 py-2 text-left font-semibold text-slate-800 ${
                  i < tableData.headers.length - 1 ? 'border-r border-slate-300' : ''
                }`}
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {tableData.rows.map((row, ri) => (
            <tr
              key={ri}
              className={ri === tableData.rows.length - 1 ? 'border-b-2 border-slate-800' : 'border-b border-slate-200'}
            >
              {row.map((cell, ci) => (
                <td
                  key={ci}
                  className={`px-3 py-2 text-slate-700 ${
                    ci < row.length - 1 ? 'border-r border-slate-200' : ''
                  } ${isNumeric(cell) ? 'text-right tabular-nums' : ''}`}
                >
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// Parse simple LaTeX tabular to HTML
function parseLatexTable(latex: string): { headers: string[]; rows: string[][] } | null {
  try {
    // Extract tabular content
    const tabularMatch = latex.match(/\\begin\{tabular\}(?:\[.*?\])?\{(.+?)\}([\s\S]+?)\\end\{tabular\}/);
    if (!tabularMatch) return null;

    const alignment = tabularMatch[1];
    const content = tabularMatch[2];

    // Split by row separators
    const rawRows = content
      .replace(/\\(hline|toprule|midrule|bottomrule)/g, '')
      .split('\\\\')
      .map(r => r.trim())
      .filter(r => r);

    if (rawRows.length === 0) return null;

    // Parse each row
    const parsedRows = rawRows.map(row => {
      return row
        .split('&')
        .map(cell => cell.trim())
        .map(cell => {
          // Clean up LaTeX commands
          return cell
            .replace(/\\textbf\{(.+?)\}/g, '$1')
            .replace(/\\textit\{(.+?)\}/g, '$1')
            .replace(/\\emph\{(.+?)\}/g, '$1')
            .replace(/\\(.+?)\{(.+?)\}/g, '$2') // Remove other commands
            .replace(/\$\$(.+?)\$\$/g, '$1') // Remove display math
            .replace(/\$(.+?)\$/g, '$1') // Remove inline math
            .trim();
        });
    });

    // First row is headers if alignment has 'l', 'c', or 'r'
    const headers = parsedRows[0] || [];
    const rows = parsedRows.slice(1);

    return { headers, rows };
  } catch (e) {
    console.error('Failed to parse LaTeX table:', e);
    return null;
  }
}

function isNumeric(value: string): boolean {
  return /^-?[\d.,]+$/.test(value.trim());
}
