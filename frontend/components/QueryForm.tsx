'use client';

import { useState, useEffect } from 'react';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { apiClient, QueryRequest } from '@/lib/api';

interface QueryFormProps {
  onSubmit: (request: QueryRequest) => void;
  isLoading: boolean;
}

export function QueryForm({ onSubmit, isLoading }: QueryFormProps) {
  const [belief, setBelief] = useState('');
  const [selectedTopics, setSelectedTopics] = useState<string[]>([]);
  const [nResults, setNResults] = useState(5);
  const [userContext, setUserContext] = useState('');
  const [availableTopics, setAvailableTopics] = useState<string[]>([]);
  const [showAdvanced, setShowAdvanced] = useState(false);

  useEffect(() => {
    // Load available topics
    apiClient.getTopics().then(data => {
      setAvailableTopics(data.topics);
    }).catch(error => {
      console.error('Error loading topics:', error);
    });
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!belief.trim()) return;

    onSubmit({
      belief: belief.trim(),
      topics: selectedTopics.length > 0 ? selectedTopics : undefined,
      n_results: nResults,
      user_context: userContext.trim() || undefined,
      verbose: true,
    });
  };

  const toggleTopic = (topic: string) => {
    setSelectedTopics(prev =>
      prev.includes(topic)
        ? prev.filter(t => t !== topic)
        : [...prev, topic]
    );
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>Find Counter-Narratives</CardTitle>
        <CardDescription>
          Challenge conventional wisdom with contrarian perspectives from Lenny's Podcast
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">
              What belief do you want to challenge?
            </label>
            <textarea
              className="w-full p-3 border rounded-md min-h-[100px] resize-y"
              placeholder="e.g., 'You need product-market fit before you can scale'"
              value={belief}
              onChange={(e) => setBelief(e.target.value)}
              disabled={isLoading}
              maxLength={500}
              required
            />
            <p className="text-xs text-muted-foreground mt-1">
              {belief.length}/500 characters
            </p>
          </div>

          {availableTopics.length > 0 && (
            <div>
              <label className="block text-sm font-medium mb-2">
                Filter by topics (optional)
              </label>
              <div className="flex flex-wrap gap-2">
                {availableTopics.map(topic => (
                  <button
                    key={topic}
                    type="button"
                    onClick={() => toggleTopic(topic)}
                    disabled={isLoading}
                    className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                      selectedTopics.includes(topic)
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
                    }`}
                  >
                    {topic.replace(/-/g, ' ')}
                  </button>
                ))}
              </div>
            </div>
          )}

          <div>
            <button
              type="button"
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="text-sm text-muted-foreground hover:text-foreground"
            >
              {showAdvanced ? '− Hide' : '+ Show'} advanced options
            </button>
          </div>

          {showAdvanced && (
            <div className="space-y-4 p-4 border rounded-md bg-muted/50">
              <div>
                <label className="block text-sm font-medium mb-2">
                  Number of perspectives: {nResults}
                </label>
                <input
                  type="range"
                  min="1"
                  max="10"
                  value={nResults}
                  onChange={(e) => setNResults(Number(e.target.value))}
                  disabled={isLoading}
                  className="w-full"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">
                  Your context (optional)
                </label>
                <textarea
                  className="w-full p-3 border rounded-md min-h-[80px] resize-y"
                  placeholder="Describe your situation for more relevant guidance..."
                  value={userContext}
                  onChange={(e) => setUserContext(e.target.value)}
                  disabled={isLoading}
                  maxLength={1000}
                />
              </div>
            </div>
          )}

          <Button
            type="submit"
            className="w-full"
            disabled={isLoading || !belief.trim()}
            size="lg"
          >
            {isLoading ? 'Searching...' : 'Find Counter-Narratives'}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
