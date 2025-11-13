import { Component, OnDestroy } from '@angular/core';
import { HttpClient, HttpClientModule } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import { SelectButtonModule } from 'primeng/selectbutton';
import { CommonModule } from '@angular/common';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { firstValueFrom } from 'rxjs';
import { ChipModule } from 'primeng/chip';

@Component({
  selector: 'app-ask-page',
  standalone: true,
  imports: [CommonModule, FormsModule, SelectButtonModule, HttpClientModule, ChipModule],
  templateUrl: './ask-page.component.html',
  styleUrl: './ask-page.component.css'
})
export class AskPageComponent implements OnDestroy {
  private readonly baseUrl = '';
  private destroyed = false;
  private requestStartedAt: number | null = null;

  question = '';
  mode: Mode = 'auto';
  readonly modes = [
    { label: 'Auto', value: 'auto' as Mode },
    { label: 'Simple', value: 'simple' as Mode },
    { label: 'Pro', value: 'pro' as Mode }
  ];
  isSubmitting = false;
  showStatusCard = false;
  hasLifted = false;
  cardState: 'idle' | 'loading' | 'success' | 'error' = 'idle';
  cardMessage = '';
  cardResult = '';
  currentTaskId: string | null = null;
  processingTimeSec: number | null = null;
  thoughtLines: string[] = [];
  thoughtsExpanded = false;

  cardResultHtml: SafeHtml | null = null;

  get modeLabel(): string {
    switch (this.mode) {
      case 'auto':
        return 'Auto';
      case 'pro':
        return 'Pro';
      default:
        return 'Simple';
    }
  }

  constructor(
    private readonly http: HttpClient,
    private readonly sanitizer: DomSanitizer
  ) {}

  async submitQuestion(): Promise<void> {
    const trimmed = this.question.trim();
    if (!trimmed || this.isSubmitting) {
      return;
    }

    this.isSubmitting = true;
    this.cardState = 'loading';
    this.cardMessage = 'Работаю над запросом';
    this.cardResult = '';
    this.cardResultHtml = null;
    this.showStatusCard = true;
    this.hasLifted = true;
    this.requestStartedAt = performance.now();
    this.processingTimeSec = null;
    this.thoughtLines = [];
    this.thoughtsExpanded = false;

    try {
      const payload: QueryPayload = { query: trimmed };
      if (this.mode !== 'auto') {
        payload.mode = this.mode;
      }

      const response = await firstValueFrom(
        this.http.post<{ task_id: string }>(`${this.baseUrl}/debug/get-mode`, payload)
      );

      this.currentTaskId = response.task_id;
      await this.pollTask(response.task_id);
    } catch (error) {
      this.cardState = 'error';
      this.cardMessage = 'Не удалось отправить запрос. Попробуйте ещё раз.';
      console.error('Submit error', error);
      this.setProcessingTime();
    } finally {
      this.isSubmitting = false;
    }
  }

  ngOnDestroy(): void {
    this.destroyed = true;
  }

  private async pollTask(taskId: string): Promise<void> {
    const pollDelay = 1500;

    while (!this.destroyed && this.currentTaskId === taskId) {
      try {
        const result = await firstValueFrom(
          this.http.get<TaskStatusResponse>(`${this.baseUrl}/debug/tasks/${taskId}`)
        );

        if (result.status === 'succeeded') {
          this.cardState = 'success';
          this.cardResult = result.result ?? 'Ответ не найден.';
          this.cardResultHtml = this.sanitizer.bypassSecurityTrustHtml(
            this.renderMarkdown(this.cardResult)
          );
          this.cardMessage = 'Результат готов';
          this.thoughtLines = this.extractThoughtLines(result.details?.thoughts);
          this.setProcessingTime();
          return;
        }

        if (result.status === 'failed' || result.status === 'error') {
          this.cardState = 'error';
          this.cardMessage = 'Запрос завершился с ошибкой.';
          this.thoughtLines = [];
          this.setProcessingTime();
          return;
        }
      } catch (error) {
        this.cardState = 'error';
        this.cardMessage = 'Ошибка при получении статуса.';
        console.error('Polling error', error);
        this.thoughtLines = [];
        this.setProcessingTime();
        return;
      }

      await this.delay(pollDelay);
    }
  }

  private setProcessingTime(): void {
    if (this.requestStartedAt === null) {
      return;
    }
    const seconds = (performance.now() - this.requestStartedAt) / 1000;
    this.processingTimeSec = Math.max(Number(seconds.toFixed(2)), 0.01);
    this.requestStartedAt = null;
  }

  toggleThoughts(): void {
    this.thoughtsExpanded = !this.thoughtsExpanded;
  }

  private extractThoughtLines(value?: string | null): string[] {
    if (!value) {
      return [];
    }
    return value
      .split(/\r?\n/)
      .map(line => line.trim())
      .filter(Boolean);
  }

  private renderMarkdown(markdown: string): string {
    const lines = markdown.split(/\r?\n/);
    const html: string[] = [];
    let inList = false;
    let inCodeBlock = false;
    const listBuffer: string[] = [];

    const flushList = () => {
      if (inList) {
        html.push('<ul>' + listBuffer.join('') + '</ul>');
        listBuffer.length = 0;
        inList = false;
      }
    };

    const escapeHtml = (value: string): string =>
      value.replace(/[&<>"']/g, char =>
        ({
          '&': '&amp;',
          '<': '&lt;',
          '>': '&gt;',
          '"': '&quot;',
          "'": '&#39;'
        }[char] ?? char)
      );

    const formatInline = (value: string): string => {
      let result = escapeHtml(value);
      result = result.replace(/`([^`]+)`/g, '<code>$1</code>');
      result = result.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
      result = result.replace(/\*([^*]+)\*/g, '<em>$1</em>');
      return result;
    };

    for (const rawLine of lines) {
      const line = rawLine.trimEnd();

      if (line.startsWith('```')) {
        if (inCodeBlock) {
          html.push('</code></pre>');
          inCodeBlock = false;
        } else {
          flushList();
          html.push('<pre><code>');
          inCodeBlock = true;
        }
        continue;
      }

      if (inCodeBlock) {
        html.push(escapeHtml(rawLine) + '\n');
        continue;
      }

      if (!line.trim()) {
        flushList();
        html.push('');
        continue;
      }

      const headingMatch = line.match(/^(#{1,6})\s+(.*)$/);
      if (headingMatch) {
        flushList();
        const level = headingMatch[1].length;
        html.push(`<h${level}>${formatInline(headingMatch[2])}</h${level}>`);
        continue;
      }

      if (/^[-*+]\s+/.test(line)) {
        if (!inList) {
          inList = true;
        }
        listBuffer.push(`<li>${formatInline(line.replace(/^[-*+]\s+/, ''))}</li>`);
        continue;
      }

      flushList();
      html.push(`<p>${formatInline(line)}</p>`);
    }

    flushList();
    if (inCodeBlock) {
      html.push('</code></pre>');
    }

    return html.join('\n');
  }

  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

interface TaskStatusResponse {
  task_id: string;
  status: 'pending' | 'running' | 'succeeded' | 'failed' | 'error';
  result?: string;
  details?: TaskDetails;
}

type Mode = 'auto' | 'simple' | 'pro';

interface QueryPayload {
  query: string;
  mode?: Mode;
}

interface TaskDetails {
  mode?: string;
  thoughts?: string;
}
