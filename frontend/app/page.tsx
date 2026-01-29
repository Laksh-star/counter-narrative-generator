'use client';

import { useState, useCallback } from 'react';
import { QueryForm } from '@/components/QueryForm';
import { ProgressIndicator } from '@/components/ProgressIndicator';
import { ResultsDisplay } from '@/components/ResultsDisplay';
import { QueryRequest, QueryResponse, ProgressUpdate } from '@/lib/api';
import { useWebSocket } from '@/lib/useWebSocket';

export default function Home() {
  const [isLoading, setIsLoading] = useState(false);
  const [currentAgent, setCurrentAgent] = useState<'workflow' | 'forethought' | 'quickaction' | 'examiner' | null>(null);
  const [currentStatus, setCurrentStatus] = useState<string>('');
  const [currentMessage, setCurrentMessage] = useState<string>('');
  const [result, setResult] = useState<QueryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleProgressUpdate = useCallback((update: ProgressUpdate) => {
    console.log('Progress update:', update);

    if (update.agent === 'workflow' && update.status === 'completed' && update.data) {
      // Final result received
      setResult(update.data as unknown as QueryResponse);
      setIsLoading(false);
      setCurrentAgent(null);
    } else if (update.status === 'error') {
      setError(update.message || 'An error occurred');
      setIsLoading(false);
      setCurrentAgent(null);
    } else {
      // Update progress
      setCurrentAgent(update.agent as any);
      setCurrentStatus(update.status);
      setCurrentMessage(update.message || '');
    }
  }, []);

  const { sendMessage, disconnect, connect, isConnected } = useWebSocket(handleProgressUpdate);

  const handleSubmit = async (request: QueryRequest) => {
    setIsLoading(true);
    setResult(null);
    setError(null);
    setCurrentAgent('workflow');
    setCurrentStatus('started');
    setCurrentMessage('Starting workflow...');

    try {
      // Connect WebSocket
      connect();

      // Wait for WebSocket to be ready (max 5 seconds)
      const maxWaitTime = 5000;
      const checkInterval = 100;
      let waited = 0;

      while (!isConnected() && waited < maxWaitTime) {
        await new Promise(resolve => setTimeout(resolve, checkInterval));
        waited += checkInterval;
      }

      if (!isConnected()) {
        throw new Error('WebSocket connection timeout');
      }

      // Send query request
      console.log('Sending query request:', request);
      sendMessage(request);
    } catch (err) {
      console.error('Error submitting query:', err);
      setError('Failed to connect to server. Please try again.');
      setIsLoading(false);
      setCurrentAgent(null);
      disconnect();
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8">
        <header className="mb-8 text-center">
          <h1 className="text-4xl font-bold mb-2">Counter-Narrative Generator</h1>
          <p className="text-lg text-muted-foreground">
            Mine contrarian perspectives from Lenny's Podcast
          </p>
        </header>

        <div className="max-w-4xl mx-auto space-y-6">
          <QueryForm onSubmit={handleSubmit} isLoading={isLoading} />

          {error && (
            <div className="p-4 bg-destructive/10 border border-destructive rounded-md">
              <p className="text-destructive font-medium">Error</p>
              <p className="text-sm mt-1">{error}</p>
            </div>
          )}

          {isLoading && (
            <ProgressIndicator
              currentAgent={currentAgent}
              status={currentStatus}
              message={currentMessage}
            />
          )}

          {result && <ResultsDisplay result={result} />}
        </div>

        <footer className="mt-12 text-center text-sm text-muted-foreground">
          <p>
            Powered by the Three-Fish Workflow inspired by the Panchatantra
            {' '}•{' '}
            <a
              href="https://github.com/Laksh-star/counter-narrative-generator"
              target="_blank"
              rel="noreferrer"
              className="underline underline-offset-4 hover:text-foreground"
            >
              GitHub
            </a>
          </p>
          <p className="mt-1">
            Built with Next.js, FastAPI, and deployed on Google Cloud Run
          </p>
        </footer>
      </div>
    </div>
  );
}
