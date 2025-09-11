import { ICellIssue } from '../../types';
import { NotebookPanel } from '@jupyterlab/notebook';

export function detectTableIssuesInCell(
  rawMarkdown: string,
  cellIndex: number,
  cellType: string
): ICellIssue[] {
  const notebookIssues: ICellIssue[] = [];

  // Check for tables without th tags
  const tableWithoutThRegex =
    /<table[^>]*>(?![\s\S]*?<th[^>]*>)[\s\S]*?<\/table>/gi;
  let match;
  while ((match = tableWithoutThRegex.exec(rawMarkdown)) !== null) {
    notebookIssues.push({
      cellIndex,
      cellType: cellType as 'code' | 'markdown',
      violationId: 'table-missing-header',
      issueContentRaw: match[0]
    });
  }

  // Check for tables without caption tags
  const tableWithoutCaptionRegex =
    /<table[^>]*>(?![\s\S]*?<caption[^>]*>)[\s\S]*?<\/table>/gi;
  while ((match = tableWithoutCaptionRegex.exec(rawMarkdown)) !== null) {
    notebookIssues.push({
      cellIndex,
      cellType: cellType as 'code' | 'markdown',
      violationId: 'table-missing-caption',
      issueContentRaw: match[0]
    });
  }

  // Check for tables with th tags but missing scope attributes
  const tableWithThRegex = /<table[^>]*>[\s\S]*?<\/table>/gi;
  while ((match = tableWithThRegex.exec(rawMarkdown)) !== null) {
    const tableHtml = match[0];
    const parser = new DOMParser();
    const doc = parser.parseFromString(tableHtml, 'text/html');
    const table = doc.querySelector('table');

    if (table) {
      const thElements = table.querySelectorAll('th');
      let hasMissingScope = false;

      thElements.forEach(th => {
        if (!th.hasAttribute('scope')) {
          hasMissingScope = true;
        }
      });

      if (hasMissingScope) {
        notebookIssues.push({
          cellIndex,
          cellType: cellType as 'code' | 'markdown',
          violationId: 'table-missing-scope',
          issueContentRaw: tableHtml
        });
      }
    }
  }

  return notebookIssues;
}

export async function analyzeTableIssues(
  panel: NotebookPanel
): Promise<ICellIssue[]> {
  const notebookIssues: ICellIssue[] = [];
  const cells = panel.content.widgets;

  for (let i = 0; i < cells.length; i++) {
    const cell = cells[i];
    if (!cell || !cell.model || cell.model.type !== 'markdown') {
      continue;
    }

    const content = cell.model.sharedModel.getSource();
    if (!content.trim()) {
      continue;
    }

    const cellIssues = detectTableIssuesInCell(content, i, 'markdown');
    notebookIssues.push(...cellIssues);
  }

  return notebookIssues;
}
