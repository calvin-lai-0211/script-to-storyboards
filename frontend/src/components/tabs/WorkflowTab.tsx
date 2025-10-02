import React, { useState } from 'react';
import { FileText, Film, Users, Camera, Image, Brain, Check, Loader2 } from 'lucide-react';

interface WorkflowTabProps {
  scriptKey: string;
}

const WorkflowTab: React.FC<WorkflowTabProps> = () => {
  const [currentStep, setCurrentStep] = useState(0);
  // scriptKey will be used when implementing actual workflow execution
  const [completedSteps, setCompletedSteps] = useState<Set<number>>(new Set());
  const [runningStep, setRunningStep] = useState<number | null>(null);

  const steps = [
    {
      id: 0,
      icon: FileText,
      title: '剧本导入',
      description: '将剧本内容导入数据库',
      color: 'blue'
    },
    {
      id: 1,
      icon: Film,
      title: '生成分镜脚本',
      description: '使用 AI 将剧本转换为分镜脚本',
      color: 'purple'
    },
    {
      id: 2,
      icon: Users,
      title: '提取资产',
      description: '从分镜中提取角色、场景、道具',
      color: 'pink'
    },
    {
      id: 3,
      icon: Camera,
      title: '生成 Prompts',
      description: '为每个资产生成图片描述',
      color: 'indigo'
    },
    {
      id: 4,
      icon: Image,
      title: '生成图片',
      description: '使用 T2I 模型生成资产图片',
      color: 'green'
    },
    {
      id: 5,
      icon: Brain,
      title: '生成 Memory',
      description: '生成剧集摘要和关键信息',
      color: 'amber'
    }
  ];

  const handleRunStep = (stepId: number) => {
    setRunningStep(stepId);
    // 模拟异步执行
    setTimeout(() => {
      setCompletedSteps(new Set([...completedSteps, stepId]));
      setRunningStep(null);
      if (stepId < steps.length - 1) {
        setCurrentStep(stepId + 1);
      }
    }, 2000);
  };

  const getStepStatus = (stepId: number) => {
    if (runningStep === stepId) return 'running';
    if (completedSteps.has(stepId)) return 'completed';
    if (stepId === currentStep) return 'current';
    return 'pending';
  };

  return (
    <div className="h-full overflow-auto p-6">
      <div className="max-w-4xl mx-auto">
        {/* 头部说明 */}
        <div className="bg-gradient-to-r from-blue-500 to-purple-500 rounded-2xl p-6 mb-8 text-white">
          <h1 className="text-2xl font-bold mb-2">生成流程控制</h1>
          <p className="text-blue-100">
            按顺序执行以下步骤，将剧本转换为完整的分镜资产
          </p>
        </div>

        {/* Steps */}
        <div className="space-y-4">
          {steps.map((step, index) => {
            const Icon = step.icon;
            const status = getStepStatus(step.id);
            const isRunning = status === 'running';
            const isCompleted = status === 'completed';
            const isCurrent = status === 'current';

            return (
              <div key={step.id} className="relative">
                {/* 连接线 */}
                {index < steps.length - 1 && (
                  <div className="absolute left-6 top-14 w-0.5 h-12 bg-slate-200"></div>
                )}

                {/* Step 卡片 */}
                <div
                  className={`relative bg-white rounded-xl border-2 transition-all duration-300 ${
                    isCompleted
                      ? 'border-green-400 shadow-lg'
                      : isCurrent
                      ? 'border-blue-400 shadow-xl'
                      : 'border-slate-200'
                  }`}
                >
                  <div className="p-6 flex items-start space-x-4">
                    {/* 图标 */}
                    <div
                      className={`flex-shrink-0 w-12 h-12 rounded-xl flex items-center justify-center transition-colors ${
                        isCompleted
                          ? 'bg-green-500'
                          : isCurrent
                          ? `bg-${step.color}-500`
                          : 'bg-slate-200'
                      }`}
                    >
                      {isRunning ? (
                        <Loader2 className="w-6 h-6 text-white animate-spin" />
                      ) : isCompleted ? (
                        <Check className="w-6 h-6 text-white" />
                      ) : (
                        <Icon
                          className={`w-6 h-6 ${
                            isCurrent ? 'text-white' : 'text-slate-400'
                          }`}
                        />
                      )}
                    </div>

                    {/* 内容 */}
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-2">
                        <h3
                          className={`text-lg font-bold ${
                            isCurrent ? 'text-slate-800' : 'text-slate-600'
                          }`}
                        >
                          Step {step.id + 1}: {step.title}
                        </h3>
                        <div className="flex items-center space-x-2">
                          {isCompleted && (
                            <span className="px-3 py-1 bg-green-100 text-green-700 text-sm rounded-full font-medium">
                              已完成
                            </span>
                          )}
                          {isCurrent && !isRunning && (
                            <button
                              onClick={() => handleRunStep(step.id)}
                              className={`px-4 py-2 bg-gradient-to-r from-${step.color}-500 to-${step.color}-600 text-white rounded-lg hover:from-${step.color}-600 hover:to-${step.color}-700 transition-colors font-medium`}
                            >
                              执行
                            </button>
                          )}
                        </div>
                      </div>
                      <p className="text-slate-600">{step.description}</p>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* 底部说明 */}
        <div className="mt-8 p-4 bg-amber-50 rounded-xl border border-amber-200">
          <p className="text-sm text-amber-800">
            <strong>注意：</strong>此流程控制面板为占位界面，实际执行功能需要集成后端 API。
          </p>
        </div>
      </div>
    </div>
  );
};

export default WorkflowTab;
