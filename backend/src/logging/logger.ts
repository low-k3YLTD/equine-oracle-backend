/**
 * Structured Logging Utility
 * Provides consistent logging across the application
 */

enum LogLevel {
  DEBUG = 'DEBUG',
  INFO = 'INFO',
  WARN = 'WARN',
  ERROR = 'ERROR',
}

interface LogEntry {
  timestamp: string;
  level: LogLevel;
  component: string;
  message: string;
  data?: any;
  error?: string;
}

class Logger {
  private component: string;
  private logLevel: LogLevel;

  constructor(component: string, logLevel: string = process.env.LOG_LEVEL || 'INFO') {
    this.component = component;
    this.logLevel = LogLevel[logLevel as keyof typeof LogLevel] || LogLevel.INFO;
  }

  private shouldLog(level: LogLevel): boolean {
    const levels = [LogLevel.DEBUG, LogLevel.INFO, LogLevel.WARN, LogLevel.ERROR];
    return levels.indexOf(level) >= levels.indexOf(this.logLevel);
  }

  private formatEntry(entry: LogEntry): string {
    return JSON.stringify(entry);
  }

  private log(level: LogLevel, message: string, data?: any): void {
    if (!this.shouldLog(level)) {
      return;
    }

    const entry: LogEntry = {
      timestamp: new Date().toISOString(),
      level,
      component: this.component,
      message,
      data,
    };

    const formatted = this.formatEntry(entry);

    switch (level) {
      case LogLevel.DEBUG:
        console.debug(formatted);
        break;
      case LogLevel.INFO:
        console.log(formatted);
        break;
      case LogLevel.WARN:
        console.warn(formatted);
        break;
      case LogLevel.ERROR:
        console.error(formatted);
        break;
    }
  }

  debug(message: string, data?: any): void {
    this.log(LogLevel.DEBUG, message, data);
  }

  info(message: string, data?: any): void {
    this.log(LogLevel.INFO, message, data);
  }

  warn(message: string, data?: any): void {
    this.log(LogLevel.WARN, message, data);
  }

  error(message: string, error?: Error | string, data?: any): void {
    const entry: LogEntry = {
      timestamp: new Date().toISOString(),
      level: LogLevel.ERROR,
      component: this.component,
      message,
      data,
      error: error instanceof Error ? error.stack : String(error),
    };

    console.error(this.formatEntry(entry));
  }
}

export { Logger, LogLevel, LogEntry };
