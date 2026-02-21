import client from './client';

export interface GeneratedTable {
  table_title: string;
  latex_code: string;
  explanation: string;
}

export interface GenerateTablesResponse {
  tables: GeneratedTable[];
}

export interface ExplainTableResponse {
  explanation: string;
}

export async function generateTables(paperId: string): Promise<GenerateTablesResponse> {
  const { data } = await client.post<GenerateTablesResponse>(`/tables/generate/${paperId}`);
  return data;
}

export async function explainTable(tableData: GeneratedTable): Promise<ExplainTableResponse> {
  const { data } = await client.post<ExplainTableResponse>(`/tables/explain`, tableData);
  return data;
}
