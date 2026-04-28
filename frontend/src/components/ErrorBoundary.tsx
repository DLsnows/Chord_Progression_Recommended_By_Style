import { Component, type ReactNode } from 'react';
import s from './ErrorBoundary.module.css';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  message: string;
}

class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, message: '' };

  static getDerivedStateFromError(error: unknown): State {
    const msg = error instanceof Error ? error.message : 'Unknown error';
    return { hasError: true, message: msg };
  }

  render(): ReactNode {
    if (this.state.hasError) {
      return (
        <div className={s.wrapper}>
          <h2 className={s.heading}>Something went wrong</h2>
          <p className={s.message}>{this.state.message}</p>
          <button className={s.reloadBtn} onClick={() => window.location.reload()}>
            Reload
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

export default ErrorBoundary;
