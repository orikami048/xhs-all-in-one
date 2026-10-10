import {
  BookOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  InfoCircleOutlined,
  ReloadOutlined,
  SafetyCertificateOutlined,
  ThunderboltOutlined,
  WarningOutlined,
} from "@ant-design/icons";
import {
  Alert,
  Badge,
  Button,
  Card,
  Collapse,
  Divider,
  Modal,
  Progress,
  Space,
  Spin,
  Tag,
  Tooltip,
  Typography,
  message as antMessage,
} from "antd";
import { useEffect, useState } from "react";

import {
  auditContentCompliance,
  fetchComplianceRules,
  sanitizeContentCompliance,
} from "../../lib/api";
import type {
  ComplianceIssue,
  ComplianceReport,
  ComplianceRuleCategory,
} from "../../lib/api";

const { Text, Paragraph, Title } = Typography;

interface ComplianceGuardCardProps {
  title: string;
  body: string;
  onApplyCleaned?: (newTitle: string, newBody: string) => void;
  compact?: boolean;
}

export function ComplianceGuardCard({
  title,
  body,
  onApplyCleaned,
  compact = false,
}: ComplianceGuardCardProps) {
  const [report, setReport] = useState<ComplianceReport | null>(null);
  const [isAuditing, setIsAuditing] = useState(false);
  const [isSanitizing, setIsSanitizing] = useState(false);
  const [rulesModalOpen, setRulesModalOpen] = useState(false);

  // Debounced audit
  useEffect(() => {
    if (!title && !body) {
      setReport(null);
      return;
    }
    const timer = setTimeout(() => {
      runAudit();
    }, 400);

    return () => clearTimeout(timer);
  }, [title, body]);

  async function runAudit() {
    if (!title && !body) return;
    setIsAuditing(true);
    try {
      const res = await auditContentCompliance({ title, body });
      setReport(res);
    } catch (e) {
      console.error("Compliance audit failed", e);
    } finally {
      setIsAuditing(false);
    }
  }

  async function handleSanitize() {
    if (!title && !body) return;
    setIsSanitizing(true);
    try {
      const res = await sanitizeContentCompliance({ title, body });
      if (onApplyCleaned) {
        onApplyCleaned(res.cleaned_title, res.cleaned_body);
      }
      antMessage.success(
        `一键净化完成！合规评分提升至 ${res.new_score} 分（已消除诱导互动与违规词）`
      );
      // Immediately run audit on cleaned result
      const newReport = await auditContentCompliance({
        title: res.cleaned_title,
        body: res.cleaned_body,
      });
      setReport(newReport);
    } catch {
      antMessage.error("合规脱敏净化失败，请检查网络或后端服务");
    } finally {
      setIsSanitizing(false);
    }
  }

  const score = report?.score ?? 100;
  const isHealthy = score >= 90;
  const isWarning = score >= 70 && score < 90;
  const isDanger = score < 70;

  const scoreColor = isHealthy ? "#52c41a" : isWarning ? "#faad14" : "#ff4d4f";
  const statusLabel = isHealthy
    ? "绿灯通过 · 极低违规风险"
    : isWarning
    ? "黄灯提醒 · 建议脱敏优化"
    : "红灯高危 · 存在平台违规封禁/限流隐患";

  return (
    <Card
      size="small"
      style={{
        marginBottom: 16,
        background: isDanger
          ? "rgba(255, 77, 79, 0.06)"
          : isWarning
          ? "rgba(250, 173, 20, 0.05)"
          : "rgba(82, 196, 26, 0.04)",
        border: `1px solid ${isDanger ? "#802829" : isWarning ? "#7a5c1b" : "#274916"}`,
        borderRadius: 8,
      }}
      title={
        <Space size={8} wrap>
          <SafetyCertificateOutlined style={{ color: scoreColor, fontSize: 16 }} />
          <Text strong style={{ fontSize: 14 }}>
            小红书官方合规审查哨所
          </Text>
          <Tag
            color={isHealthy ? "success" : isWarning ? "warning" : "error"}
            style={{ fontWeight: 600, borderRadius: 10, padding: "0 8px" }}
          >
            {score} 分 · {statusLabel}
          </Tag>
          {isAuditing && <Spin size="small" />}
        </Space>
      }
      extra={
        <Space size={8}>
          <Button
            size="small"
            icon={<BookOutlined />}
            onClick={() => setRulesModalOpen(true)}
          >
            合规避坑手册
          </Button>
          {onApplyCleaned && (report?.issues?.length ?? 0) > 0 && (
            <Button
              size="small"
              type="primary"
              icon={<ThunderboltOutlined />}
              loading={isSanitizing}
              onClick={handleSanitize}
              style={{
                background: "#722ed1",
                borderColor: "#722ed1",
              }}
            >
              一键合规净化
            </Button>
          )}
        </Space>
      }
    >
      <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        {/* Violation Warning / Notice */}
        {report && report.issues && report.issues.length > 0 ? (
          <div>
            <Alert
              type={isDanger ? "error" : "warning"}
              showIcon
              icon={isDanger ? <ExclamationCircleOutlined /> : <WarningOutlined />}
              message={
                <Space>
                  <Text strong>
                    检测到 {report.issues.length} 处违规或降权风险点（包含 {report.danger_count} 个高危项）
                  </Text>
                </Space>
              }
              description={
                <div style={{ marginTop: 6, display: "flex", flexDirection: "column", gap: 8 }}>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    小红书 2026 算法严查「诱导点赞/评论扣1/求藏/站外导流」，被查出将直接判定违规并转为仅自己可见（私密）或全面限流！
                  </Text>
                  <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                    {report.issues.map((issue, idx) => (
                      <div
                        key={idx}
                        style={{
                          background: "rgba(0,0,0,0.25)",
                          padding: "6px 10px",
                          borderRadius: 6,
                          borderLeft: `3px solid ${issue.severity === "high" ? "#ff4d4f" : "#faad14"}`,
                        }}
                      >
                        <Space size={6} wrap style={{ marginBottom: 2 }}>
                          <Tag color={issue.severity === "high" ? "red" : "orange"} style={{ margin: 0 }}>
                            {issue.severity === "high" ? "高危违规" : "轻度提醒"}
                          </Tag>
                          <Tag style={{ margin: 0 }}>{issue.category_name}</Tag>
                          <Text strong style={{ color: "#ff7875" }}>
                            命中词:「{issue.matched_text}」
                          </Text>
                        </Space>
                        <div style={{ fontSize: 12, color: "rgba(255,255,255,0.75)" }}>
                          💡 <b>修改建议</b>：{issue.advice}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              }
            />
          </div>
        ) : (
          <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "4px 0" }}>
            <CheckCircleOutlined style={{ color: "#52c41a", fontSize: 16 }} />
            <Text style={{ fontSize: 13, color: "rgba(255,255,255,0.8)" }}>
              文案未发现「诱导点赞/求藏/评论暗号/极限词/站外导流」等违规特征，符合小红书社区规范。
            </Text>
          </div>
        )}

        {/* Quick Tips */}
        {!compact && (
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              fontSize: 12,
              color: "rgba(255,255,255,0.45)",
              borderTop: "1px dashed rgba(255,255,255,0.1)",
              paddingTop: 8,
            }}
          >
            <span>
              💡 核心避坑：勿在标题或正文中出现“扣1”、“求赞求藏”、“私发领取”，请以真实的交流问答替代互动引导。
            </span>
            <Button
              type="link"
              size="small"
              icon={<ReloadOutlined />}
              onClick={runAudit}
              loading={isAuditing}
              style={{ padding: 0 }}
            >
              重新审查
            </Button>
          </div>
        )}
      </div>

      <ComplianceRulesModal
        open={rulesModalOpen}
        onClose={() => setRulesModalOpen(false)}
      />
    </Card>
  );
}

export function ComplianceRulesModal({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const [categories, setCategories] = useState<ComplianceRuleCategory[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (open) {
      loadRules();
    }
  }, [open]);

  async function loadRules() {
    setIsLoading(true);
    try {
      const data = await fetchComplianceRules();
      setCategories(data.categories);
    } catch {
      // Fallback display if API encounters issue
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <Modal
      title={
        <Space>
          <SafetyCertificateOutlined style={{ color: "#722ed1", fontSize: 20 }} />
          <span style={{ fontSize: 16, fontWeight: 600 }}>
            📕 小红书官方社区规范与避坑避禁手册（2026 最新版）
          </span>
        </Space>
      }
      open={open}
      onCancel={onClose}
      footer={[
        <Button key="close" type="primary" onClick={onClose}>
          我已知晓并遵守
        </Button>,
      ]}
      width={780}
    >
      <Spin spinning={isLoading}>
        <div style={{ display: "flex", flexDirection: "column", gap: 16, marginTop: 12 }}>
          <Alert
            type="info"
            showIcon
            message="🛡️ 为什么发布后状态会变成「私密」或被警告「违规诱导点赞」？"
            description={
              <div>
                <Paragraph style={{ margin: "4px 0", fontSize: 13 }}>
                  小红书部署了严格的多模态 NLP 与 OCR 识别引擎。当文案中出现<b>「扣1、评论区留下xx、求赞求收藏、私信发你、领取网站」</b>等词汇时，
                  系统会判定为<b>「违规诱导互动」</b>或<b>「低质引流」</b>，触发以下阶梯处罚：
                </Paragraph>
                <ul style={{ paddingLeft: 20, margin: "4px 0", fontSize: 12, color: "rgba(255,255,255,0.7)" }}>
                  <li><b>直接转为仅自己可见（私密）</b>：外部用户搜索不到，主页不显示，零自然流量。</li>
                  <li><b>静默限流（降权）</b>：笔记发布成功但不再进入推荐公域信息流。</li>
                  <li><b>创作者违规扣分</b>：多次诱导互动将影响账号健康度与带货发布权限。</li>
                </ul>
              </div>
            }
          />

          <Title level={5} style={{ margin: "4px 0 0" }}>
            📌 四大重点审查红线与合规改造范例：
          </Title>

          <Collapse
            defaultActiveKey={["engagement_bait", "medical_claims"]}
            items={[
              {
                key: "engagement_bait",
                label: (
                  <Space>
                    <Tag color="red">重点严查</Tag>
                    <Text strong>1. 诱导他人点赞、评论与收藏互动（违反社区互动真实性）</Text>
                  </Space>
                ),
                children: (
                  <div style={{ display: "flex", flexDirection: "column", gap: 8, fontSize: 13 }}>
                    <div>
                      <Text strong style={{ color: "#ff4d4f" }}>❌ 违规特征（绝对禁发）：</Text>
                      <Paragraph type="secondary" style={{ margin: "2px 0 0" }}>
                        “需要的宝子在评论区扣个【1】”、“点赞收藏后私发你入口”、“评论区留言我一个个回复发你们”、“动动发财小手点个小心心”
                      </Paragraph>
                    </div>
                    <div>
                      <Text strong style={{ color: "#52c41a" }}>✅ 合规表达（高权重点赞方式）：</Text>
                      <Paragraph type="secondary" style={{ margin: "2px 0 0" }}>
                        提出具体有价值的开放式话题激发自然讨论，例如：“大家平时日常调理或者家里人遇到类似情况，最常参考的是哪张经方？欢迎在评论区一起交流探讨自用体会~”
                      </Paragraph>
                    </div>
                    <Alert
                      type="warning"
                      message="处罚机制：触发系统「引导他人互动」违规通知，单篇笔记直接判私密，多次违规冻结互动功能。"
                      style={{ fontSize: 12 }}
                    />
                  </div>
                ),
              },
              {
                key: "medical_claims",
                label: (
                  <Space>
                    <Tag color="orange">医疗红线</Tag>
                    <Text strong>2. 医疗与中医绝对化疗效宣称（规避虚假宣传）</Text>
                  </Space>
                ),
                children: (
                  <div style={{ display: "flex", flexDirection: "column", gap: 8, fontSize: 13 }}>
                    <div>
                      <Text strong style={{ color: "#ff4d4f" }}>❌ 违规特征：</Text>
                      <Paragraph type="secondary" style={{ margin: "2px 0 0" }}>
                        “包治百病”、“百分百根治”、“神医神方”、“立竿见影药到病除”、“治愈所有慢性病”
                      </Paragraph>
                    </div>
                    <div>
                      <Text strong style={{ color: "#52c41a" }}>✅ 合规表达：</Text>
                      <Paragraph type="secondary" style={{ margin: "2px 0 0" }}>
                        以个人学习倪海厦经方心得、日常温阳散寒经验交流为切入点，文末必须附带声明：
                        <i>【温馨提示：本笔记仅供中医药经方学术交流与个人笔记整理，个体体质不同，如有身体不适请务必遵医嘱线下面诊辨证】</i>
                      </Paragraph>
                    </div>
                  </div>
                ),
              },
              {
                key: "external_diversion",
                label: (
                  <Space>
                    <Tag color="purple">引流违规</Tag>
                    <Text strong>3. 站外导流与联系方式引流（破坏平台生态）</Text>
                  </Space>
                ),
                children: (
                  <div style={{ display: "flex", flexDirection: "column", gap: 8, fontSize: 13 }}>
                    <div>
                      <Text strong style={{ color: "#ff4d4f" }}>❌ 违规特征：</Text>
                      <Paragraph type="secondary" style={{ margin: "2px 0 0" }}>
                        “加我vx”、“关注公众号xxx”、“看我主页签名链接”、“私信发你网盘链接/微信”
                      </Paragraph>
                    </div>
                    <div>
                      <Text strong style={{ color: "#52c41a" }}>✅ 合规表达：</Text>
                      <Paragraph type="secondary" style={{ margin: "2px 0 0" }}>
                        把工具的架构、经方目录直接以图片或文本精华形式呈现，吸引同频爱好者自然在评论区探讨交流。
                      </Paragraph>
                    </div>
                  </div>
                ),
              },
              {
                key: "extreme_words",
                label: (
                  <Space>
                    <Tag color="blue">广告法</Tag>
                    <Text strong>4. 新广告法极限词（涉嫌夸大虚假宣传）</Text>
                  </Space>
                ),
                children: (
                  <div style={{ display: "flex", flexDirection: "column", gap: 8, fontSize: 13 }}>
                    <div>
                      <Text strong style={{ color: "#ff4d4f" }}>❌ 违规特征：</Text>
                      <Paragraph type="secondary" style={{ margin: "2px 0 0" }}>
                        “全网第一”、“最强神器”、“史诗级天花板”、“独一无二绝无仅有”
                      </Paragraph>
                    </div>
                    <div>
                      <Text strong style={{ color: "#52c41a" }}>✅ 合规表达：</Text>
                      <Paragraph type="secondary" style={{ margin: "2px 0 0" }}>
                        改为客观陈述，如：“自己花心血梳理的实用速查工具”、“方便对照倪师方剂批注与剂量”
                      </Paragraph>
                    </div>
                  </div>
                ),
              },
            ]}
          />
        </div>
      </Spin>
    </Modal>
  );
}
