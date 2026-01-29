'use client';

import { Card, CardContent } from './ui/card';

interface ProgressIndicatorProps {
  currentAgent: 'workflow' | 'forethought' | 'quickaction' | 'examiner' | null;
  status: string;
  message?: string;
}

const AGENT_INFO = {
  workflow: {
    name: 'Workflow',
    description: 'Initializing workflow',
    icon: '⚙️',
  },
  forethought: {
    name: 'Forethought (Scout)',
    description: 'Searching for contrarian perspectives',
    icon: '🔍',
  },
  quickaction: {
    name: 'Quickaction (Miner)',
    description: 'Structuring arguments and identifying themes',
    icon: '⛏️',
  },
  examiner: {
    name: 'Examiner (Architect)',
    description: 'Synthesizing debate and creating framework',
    icon: '🏛️',
  },
};

export function ProgressIndicator({ currentAgent, status, message }: ProgressIndicatorProps) {
  if (!currentAgent) return null;

  const agentInfo = AGENT_INFO[currentAgent] || AGENT_INFO.workflow;
  const isError = status === 'error';
  const isCompleted = status === 'completed';

  return (
    <Card className={`w-full ${isError ? 'border-destructive' : ''}`}>
      <CardContent className="p-6">
        <div className="flex items-center space-x-4">
          <div className="text-4xl">{agentInfo.icon}</div>
          <div className="flex-1">
            <h3 className="font-semibold text-lg">{agentInfo.name}</h3>
            <p className="text-sm text-muted-foreground">
              {message || agentInfo.description}
            </p>
            {!isError && !isCompleted && (
              <div className="mt-2 flex items-center space-x-2">
                <div className="animate-spin h-4 w-4 border-2 border-primary border-t-transparent rounded-full"></div>
                <span className="text-xs text-muted-foreground">Processing...</span>
              </div>
            )}
            {isCompleted && (
              <div className="mt-2 flex items-center space-x-2 text-green-600">
                <span className="text-sm">✓ Completed</span>
              </div>
            )}
            {isError && (
              <div className="mt-2 flex items-center space-x-2 text-destructive">
                <span className="text-sm">✗ Error</span>
              </div>
            )}
          </div>
        </div>

        {/* Progress bar showing stages */}
        <div className="mt-4 flex items-center space-x-2">
          {['forethought', 'quickaction', 'examiner'].map((agent, index) => (
            <div key={agent} className="flex-1 flex items-center">
              <div
                className={`h-2 flex-1 rounded-full transition-colors ${
                  currentAgent === agent
                    ? 'bg-primary animate-pulse'
                    : agent === 'forethought' ||
                      (agent === 'quickaction' && ['quickaction', 'examiner'].includes(currentAgent || ''))
                    ? 'bg-primary/50'
                    : 'bg-muted'
                }`}
              ></div>
              {index < 2 && <div className="w-2"></div>}
            </div>
          ))}
        </div>

        <div className="mt-2 flex justify-between text-xs text-muted-foreground">
          <span>Scout</span>
          <span>Miner</span>
          <span>Architect</span>
        </div>
      </CardContent>
    </Card>
  );
}
