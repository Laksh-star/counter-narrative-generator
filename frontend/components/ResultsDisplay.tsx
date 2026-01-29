'use client';

import { useSearchParams } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { QueryResponse } from '@/lib/api';

interface ResultsDisplayProps {
  result: QueryResponse;
}

export function ResultsDisplay({ result }: ResultsDisplayProps) {
  const searchParams = useSearchParams();
  const forethought = result.forethought;
  const quickaction = result.quickaction;
  const examiner = result.examiner;
  const debugFlag = searchParams?.get('debug') || '';
  const showDebug = debugFlag === '1' || debugFlag.toLowerCase() === 'true';

  // Handle both field names for contrarian perspectives
  const contrarianPerspectives = forethought.contrarian_perspectives || forethought.contrarian_findings || [];

  return (
    <div className="space-y-6">
      {showDebug && (
        <Card className="border-yellow-500 bg-yellow-50 dark:bg-yellow-900/10">
          <CardHeader>
            <CardTitle className="text-sm">🐛 Debug: Forethought Data</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="text-xs overflow-auto max-h-40">
              {JSON.stringify(forethought, null, 2)}
            </pre>
          </CardContent>
        </Card>
      )}

      {/* Metadata */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex justify-between items-center text-sm">
            <div>
              <span className="font-medium">Tokens used:</span>{' '}
              <span className="text-muted-foreground">
                {result.metadata.total_tokens.total.toLocaleString()}
              </span>
            </div>
            <div>
              <span className="font-medium">Execution time:</span>{' '}
              <span className="text-muted-foreground">
                {(result.metadata.execution_time_ms / 1000).toFixed(2)}s
              </span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Forethought Results */}
      {contrarianPerspectives.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>🔍 Contrarian Perspectives Found</CardTitle>
            <CardDescription>
              Perspectives that challenge: {result.conventional_wisdom}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {contrarianPerspectives.map((finding: any, index: number) => (
              <div key={index} className="border-l-4 border-primary pl-4 py-3 space-y-2">
                {/* Guest and Episode Info */}
                <div className="flex items-start justify-between">
                  <div>
                    <div className="font-semibold text-lg">{finding.guest_name || finding.guest || 'Unknown Guest'}</div>
                    {(finding.episode_id || finding.citation) && (
                      <div className="text-xs text-muted-foreground mt-1">
                        {finding.episode_id && <span>Episode: {finding.episode_id}</span>}
                        {finding.episode_id && finding.citation && <span> • </span>}
                        {finding.citation && <span>{finding.citation}</span>}
                      </div>
                    )}
                  </div>
                  {finding.relevance_score && (
                    <div className="text-xs font-medium px-2 py-1 bg-primary/10 text-primary rounded">
                      Score: {finding.relevance_score}/10
                    </div>
                  )}
                </div>

                {/* Contrarian Position */}
                {(finding.contrarian_position || finding.position || finding.perspective) && (
                  <div>
                    <span className="text-xs font-medium text-muted-foreground">Position:</span>
                    <p className="text-sm mt-1">{finding.contrarian_position || finding.position || finding.perspective}</p>
                  </div>
                )}

                {/* Quote */}
                {(finding.quote || finding.evidence) && (
                  <div className="bg-muted/50 p-3 rounded-md border-l-2 border-primary">
                    <p className="text-sm italic">"{finding.quote || finding.evidence}"</p>
                  </div>
                )}

                {/* Reasoning */}
                {finding.reasoning_hint && (
                  <div>
                    <span className="text-xs font-medium text-muted-foreground">Reasoning:</span>
                    <p className="text-sm mt-1">{finding.reasoning_hint}</p>
                  </div>
                )}

                {/* Timestamp if available */}
                {finding.timestamp && (
                  <div className="text-xs text-muted-foreground">
                    Timestamp: {finding.timestamp}
                  </div>
                )}
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Quickaction Results */}
      {quickaction.structured_arguments && quickaction.structured_arguments.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>⛏️ Structured Arguments</CardTitle>
            <CardDescription>Key arguments organized by theme</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {quickaction.structured_arguments.map((arg: any, index: number) => (
              <div key={index} className="space-y-3 pb-6 border-b last:border-b-0">
                <h4 className="font-semibold text-lg">{arg.core_argument}</h4>

                {arg.reasoning && arg.reasoning.length > 0 && (
                  <div>
                    <span className="text-xs font-medium text-muted-foreground">Reasoning:</span>
                    <ul className="list-disc list-inside space-y-1 mt-1">
                      {arg.reasoning.map((reason: string, i: number) => (
                        <li key={i} className="text-sm">{reason}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {arg.evidence && (
                  <div className="p-3 bg-muted rounded-md">
                    <span className="text-xs font-medium">Evidence:</span>
                    <p className="text-sm mt-1">{arg.evidence}</p>
                  </div>
                )}

                {arg.best_quote && (
                  <div className="pl-4 border-l-2 border-primary">
                    <p className="text-sm italic">"{arg.best_quote}"</p>
                  </div>
                )}

                {arg.conditions && (
                  <div className="text-xs space-y-1">
                    {arg.conditions.applies_when && (
                      <div>
                        <span className="font-medium text-green-700">✓ Applies when:</span>{' '}
                        <span className="text-muted-foreground">{arg.conditions.applies_when}</span>
                      </div>
                    )}
                    {arg.conditions.does_not_apply_when && (
                      <div>
                        <span className="font-medium text-red-700">✗ Does not apply when:</span>{' '}
                        <span className="text-muted-foreground">{arg.conditions.does_not_apply_when}</span>
                      </div>
                    )}
                  </div>
                )}

                {arg.confidence && (
                  <div className="text-xs">
                    <span className="font-medium">Confidence:</span>{' '}
                    <span className={`px-2 py-1 rounded ${
                      arg.confidence === 'High' ? 'bg-green-100 text-green-800' :
                      arg.confidence === 'Medium' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {arg.confidence}
                    </span>
                  </div>
                )}
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Examiner Results */}
      {examiner && (
        <Card className="border-2 border-primary">
          <CardHeader>
            <CardTitle>🏛️ Synthesis & Analysis</CardTitle>
            <CardDescription>Deep analysis and decision framework</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Steelmanned Arguments */}
            {examiner.steelman_conventional && (
              <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-md">
                <h4 className="font-semibold mb-2 text-green-900 dark:text-green-100">
                  💪 Strongest Case for Conventional Wisdom
                </h4>
                <p className="text-sm text-green-800 dark:text-green-200 mb-2">
                  {examiner.steelman_conventional.strongest_case}
                </p>
                {examiner.steelman_conventional.supporting_evidence && (
                  <div className="text-xs text-green-700 dark:text-green-300 mt-2">
                    <span className="font-medium">Evidence:</span> {examiner.steelman_conventional.supporting_evidence}
                  </div>
                )}
              </div>
            )}

            {examiner.steelman_contrarian && (
              <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-md">
                <h4 className="font-semibold mb-2 text-blue-900 dark:text-blue-100">
                  💪 Strongest Case for Contrarian View
                </h4>
                <p className="text-sm text-blue-800 dark:text-blue-200 mb-2">
                  {examiner.steelman_contrarian.strongest_case}
                </p>
                {examiner.steelman_contrarian.supporting_evidence && (
                  <div className="text-xs text-blue-700 dark:text-blue-300 mt-2">
                    <span className="font-medium">Evidence:</span> {examiner.steelman_contrarian.supporting_evidence}
                  </div>
                )}
              </div>
            )}

            {examiner.real_disagreement && (
              <div className="p-4 bg-amber-50 dark:bg-amber-900/20 rounded-md">
                <h4 className="font-semibold mb-2 text-amber-900 dark:text-amber-100">
                  🎯 Real Disagreement
                </h4>
                <p className="text-sm text-amber-800 dark:text-amber-200">{examiner.real_disagreement}</p>
              </div>
            )}

            {/* When Each Applies */}
            {(examiner.when_conventional_applies || examiner.when_contrarian_applies) && (
              <div>
                <h4 className="font-semibold text-lg mb-3">Decision Framework</h4>
                <div className="space-y-4">
                  {examiner.when_conventional_applies && examiner.when_conventional_applies.length > 0 && (
                    <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-md">
                      <h5 className="font-medium mb-2 text-green-900 dark:text-green-100">
                        ✓ When Conventional Wisdom Applies
                      </h5>
                      <ul className="list-disc list-inside space-y-1 text-sm text-green-800 dark:text-green-200">
                        {examiner.when_conventional_applies.map((item: string, index: number) => (
                          <li key={index}>{item}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {examiner.when_contrarian_applies && examiner.when_contrarian_applies.length > 0 && (
                    <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-md">
                      <h5 className="font-medium mb-2 text-blue-900 dark:text-blue-100">
                        ✓ When Contrarian View Applies
                      </h5>
                      <ul className="list-disc list-inside space-y-1 text-sm text-blue-800 dark:text-blue-200">
                        {examiner.when_contrarian_applies.map((item: string, index: number) => (
                          <li key={index}>{item}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            )}

            {examiner.meta_lesson && (
              <div className="p-4 bg-purple-50 dark:bg-purple-900/20 rounded-md">
                <h4 className="font-semibold mb-2 text-purple-900 dark:text-purple-100">
                  💡 Meta-Lesson
                </h4>
                <p className="text-sm text-purple-800 dark:text-purple-200">{examiner.meta_lesson}</p>
              </div>
            )}

            {examiner.questions_to_ask && examiner.questions_to_ask.length > 0 && (
              <div>
                <h4 className="font-semibold text-lg mb-2">Questions to Ask Yourself</h4>
                <ul className="space-y-2">
                  {examiner.questions_to_ask.map((question: string, index: number) => (
                    <li key={index} className="flex items-start">
                      <span className="text-primary mr-2">•</span>
                      <span className="text-sm">{question}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {examiner.warning_signs && examiner.warning_signs.length > 0 && (
              <div className="p-4 bg-red-50 dark:bg-red-900/20 rounded-md">
                <h4 className="font-semibold mb-2 text-red-900 dark:text-red-100">
                  ⚠️ Warning Signs
                </h4>
                <ul className="list-disc list-inside space-y-1 text-sm text-red-800 dark:text-red-200">
                  {examiner.warning_signs.map((sign: string, index: number) => (
                    <li key={index}>{sign}</li>
                  ))}
                </ul>
              </div>
            )}

            {examiner.summary && (
              <div className="p-4 bg-muted rounded-md border-l-4 border-primary">
                <h4 className="font-semibold mb-2">Summary</h4>
                <p className="text-sm">{examiner.summary}</p>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
