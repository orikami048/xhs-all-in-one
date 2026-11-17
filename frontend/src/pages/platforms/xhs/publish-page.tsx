import {
  CalendarOutlined,
  CheckCircleOutlined,
  DeleteOutlined,
  ExclamationCircleOutlined,
  EyeOutlined,
  PictureOutlined,
  PlayCircleOutlined,
  ReloadOutlined,
  SaveOutlined,
  SendOutlined,
  RobotOutlined,
  MobileOutlined,
  ThunderboltOutlined,
  KeyOutlined,
} from "@ant-design/icons";
import {
  Alert,
  Button,
  Card,
  Col,
  DatePicker,
  Empty,
  Form,
  Image,
  Input,
  List,
  Modal,
  Popconfirm,
  Row,
  Select,
  Space,
  Spin,
  Tag,
  Typography,
  Segmented,
  message as antdMessage,
} from "antd";
import dayjs from "dayjs";
import type { Dayjs } from "dayjs";
import { useEffect, useState } from "react";

import { ComplianceGuardCard } from "../../../components/compliance/compliance-guard";
import { PageHeader } from "../../../components/layout/app-shell";
import { XhsMobilePreview } from "../../../components/preview/xhs-mobile-preview";
import {
  deletePublishJob,
  fetchAccounts,
  fetchPublishAssets,
  fetchPublishJob,
  fetchPublishJobs,
  publishJobToCreator,
  updatePublishJob,
  mcpPublishJob,
  generateCopilotJob,
  launchBrowserLogin,
} from "../../../lib/api";
import { formatShanghaiTime } from "../../../lib/time";
import type { PlatformAccount, PublishAsset, PublishJob } from "../../../types";

const { Title, Text, Paragraph } = Typography;

const STATUS_TAG_MAP: Record<string, { color: string; label: string }> = {
  pending: { color: "blue", label: "待发布" },
  uploading: { color: "processing", label: "上传中" },
  publishing: { color: "processing", label: "发布中" },
  published: { color: "green", label: "已发布" },
  failed: { color: "red", label: "失败" },
  cancelled: { color: "default", label: "已取消" },
  scheduled: { color: "gold", label: "已定时" },
};

function getStatusTag(status: string) {
  const mapping = STATUS_TAG_MAP[status] ?? { color: "default", label: status };
  return <Tag color={mapping.color}>{mapping.label}</Tag>;
}

function toLocalInputValue(value?: string | null): string {
  if (!value) return "";
  return value.replace("T", " ").slice(0, 16).replace(" ", "T");
}

function isFutureScheduledAt(value: string): boolean {
  if (!value) return false;
  const timestamp = new Date(value).getTime();
  return Number.isFinite(timestamp) && timestamp > Date.now();
}

const panelStyle: React.CSSProperties = {
  background: "#1a1a1a",
  borderRadius: 8,
  border: "1px solid #303030",
};

const cardBodyStyle: React.CSSProperties = { padding: 16 };

export function XhsPublishPage() {
  const [jobs, setJobs] = useState<PublishJob[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [assets, setAssets] = useState<PublishAsset[]>([]);
  const [accounts, setAccounts] = useState<PlatformAccount[]>([]);
  const [selectedJobId, setSelectedJobId] = useState<number | null>(null);
  const [selectedAccountId, setSelectedAccountId] = useState<number | null>(null);
  const [publishMode, setPublishMode] = useState<"immediate" | "scheduled">("immediate");
  const [scheduledAt, setScheduledAt] = useState("");
  const [topicsText, setTopicsText] = useState("");
  const [location, setLocation] = useState("");
  const [privacyChoice, setPrivacyChoice] = useState<"public" | "private">("public");
  const [isLoading, setIsLoading] = useState(true);
  const [isDetailLoading, setIsDetailLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isPublishing, setIsPublishing] = useState(false);
  const [isMcpPublishing, setIsMcpPublishing] = useState(false);
  const [isCopilotModalOpen, setIsCopilotModalOpen] = useState(false);
  const [isGeneratingCopilot, setIsGeneratingCopilot] = useState(false);
  const [copilotTopic, setCopilotTopic] = useState("");
  const [previewTab, setPreviewTab] = useState<"phone" | "meta">("phone");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const creatorAccounts = accounts.filter((a) => a.platform === "xhs" && a.sub_type === "creator");
  const filteredJobs = statusFilter === "all" ? jobs : jobs.filter((j) => j.status === statusFilter);
  const selectedJob = jobs.find((job) => job.id === selectedJobId) ?? null;
  const imageAssets = assets.filter((a) => a.asset_type === "image");
  const videoAssets = assets.filter((a) => a.asset_type === "video");
  const hasAnyAsset = assets.length > 0;
  const isScheduleValid = publishMode !== "scheduled" || isFutureScheduledAt(scheduledAt);
  const isPublishLocked = selectedJob ? ["publishing", "published", "scheduled"].includes(selectedJob.status) : false;
  const hasAccount = Boolean(selectedAccountId || (selectedJob && selectedJob.platform_account_id && selectedJob.platform_account_id > 0));
  const readyChecks = [
    { label: "标题已填写", ok: Boolean(selectedJob?.title?.trim()) },
    { label: "已选择发布账号", ok: hasAccount },
    { label: "草稿包含至少一张图片或一个视频", ok: hasAnyAsset },
    { label: "定时时间是未来时间", ok: isScheduleValid },
    { label: "任务状态可发布", ok: Boolean(selectedJob && !isPublishLocked) },
  ];
  const canPublish = Boolean(selectedJob && readyChecks.every((check) => check.ok));

  function parseTopics(value: string): string[] {
    return value.split(/[,\n，]/).map((item) => item.trim()).filter(Boolean);
  }

  function applyJob(job: PublishJob) {
    setSelectedJobId(job.id);
    setPublishMode(job.publish_mode === "scheduled" ? "scheduled" : "immediate");
    setScheduledAt(toLocalInputValue(job.scheduled_at));
    setTopicsText((job.publish_options?.topics ?? []).join("，"));
    setLocation(job.publish_options?.location ?? "");
    if (job.platform_account_id && job.platform_account_id > 0) {
      setSelectedAccountId(job.platform_account_id);
    } else {
      setSelectedAccountId(null);
    }
    if (typeof job.publish_options?.is_private === "boolean") {
      setPrivacyChoice(job.publish_options.is_private ? "private" : "public");
    } else if (job.publish_options?.privacy_type === 1) {
      setPrivacyChoice("private");
    } else {
      setPrivacyChoice("public");
    }
    setMessage(null);
    setError(null);
  }

  async function loadAssets(jobId: number) {
    const result = await fetchPublishAssets(jobId);
    setAssets(result.items);
  }

  async function loadAccounts() {
    try {
      const result = await fetchAccounts("xhs");
      setAccounts(result);
    } catch {
      setAccounts([]);
    }
  }

  async function loadJobs() {
    setIsLoading(true);
    setError(null);
    try {
      const result = await fetchPublishJobs("xhs");
      setJobs(result.items);
      if (result.items.length > 0) {
        const current = selectedJobId ? result.items.find((job) => job.id === selectedJobId) : null;
        const nextJob = current ?? result.items[0];
        applyJob(nextJob);
        await loadAssets(nextJob.id);
      } else {
        setSelectedJobId(null);
        setAssets([]);
      }
    } catch {
      setError("发布任务加载失败。");
    } finally {
      setIsLoading(false);
    }
  }

  async function handleSelect(job: PublishJob) {
    setIsDetailLoading(true);
    try {
      const detail = await fetchPublishJob(job.id);
      applyJob(detail);
      await loadAssets(detail.id);
    } catch {
      setError("发布任务详情加载失败。");
    } finally {
      setIsDetailLoading(false);
    }
  }

  async function handleSave() {
    if (!selectedJob) return;
    setIsSaving(true);
    setError(null);
    setMessage(null);
    try {
      const updated = await updatePublishJob(selectedJob.id, {
        platform_account_id: selectedAccountId,
        publish_mode: publishMode,
        scheduled_at: publishMode === "scheduled" && scheduledAt ? scheduledAt.replace("T", " ") : null,
        topics: parseTopics(topicsText),
        location: location.trim() || null,
        is_private: privacyChoice === "private",
      });
      setJobs((current) => current.map((job) => (job.id === updated.id ? updated : job)));
      applyJob(updated);
      setMessage(`发布参数已保存。`);
    } catch {
      setError("发布参数保存失败。");
    } finally {
      setIsSaving(false);
    }
  }

  async function handlePublish() {
    if (!selectedJob) return;
    setIsPublishing(true);
    setError(null);
    setMessage(null);
    try {
      await updatePublishJob(selectedJob.id, {
        platform_account_id: selectedAccountId,
        publish_mode: publishMode,
        scheduled_at: publishMode === "scheduled" && scheduledAt ? scheduledAt.replace("T", " ") : null,
        topics: parseTopics(topicsText),
        location: location.trim() || null,
        is_private: privacyChoice === "private",
      });
      const updated = await publishJobToCreator(selectedJob.id);
      setJobs((current) => current.map((job) => (job.id === updated.id ? updated : job)));
      applyJob(updated);
      setMessage(updated.status === "scheduled" ? `发布任务 #${updated.id} 已定时。` : `发布任务 #${updated.id} 已提交。`);
    } catch (err: unknown) {
      const d = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(d || "发布失败，请确认 Creator 账号和素材状态。");
      try {
        const refreshed = await fetchPublishJob(selectedJob.id);
        setJobs((current) => current.map((job) => (job.id === refreshed.id ? refreshed : job)));
        setSelectedJobId(refreshed.id);
      } catch { /* keep original error */ }
    } finally {
      setIsPublishing(false);
    }
  }

  async function handleMcpPublish() {
    if (!selectedJob) return;
    setIsMcpPublishing(true);
    setError(null);
    setMessage(null);
    try {
      antdMessage.loading({
        content: "🚀 正在调起 D 盘 Camoufox 防封环境全自动发布...（如遇滑块验证，请在弹出的浏览器中顺手滑动）",
        key: "mcp-publish",
        duration: 0,
      });
      const res = await mcpPublishJob(selectedJob.id);
      if (res.ok) {
        antdMessage.success({
          content: "🎉 恭喜！通过 AliasMode 防封环境全自动发布成功！",
          key: "mcp-publish",
          duration: 5,
        });
        await loadJobs();
      } else {
        antdMessage.error({
          content: `发布未完成: ${res.message || res.error}`,
          key: "mcp-publish",
          duration: 5,
        });
        setError(res.error || res.message);
        await loadJobs();
      }
    } catch (err: unknown) {
      const d = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      antdMessage.error({ content: d || "MCP 自动化调用失败", key: "mcp-publish", duration: 4 });
      setError(d || "MCP 自动化调用失败");
    } finally {
      setIsMcpPublishing(false);
    }
  }

  async function handleDeleteJob() {
    if (!selectedJob) return;
    setError(null);
    setMessage(null);
    try {
      await deletePublishJob(selectedJob.id);
      setJobs((current) => current.filter((j) => j.id !== selectedJob.id));
      setSelectedJobId(null);
      setAssets([]);
      setSelectedAccountId(null);
      setMessage("发布任务已删除。");
    } catch (err: unknown) {
      const d = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(d || "发布任务删除失败。");
    }
  }

  async function handleRunCopilot(targetTopic?: string) {
    const topicToUse = (targetTopic || copilotTopic || "AI生产力工具").trim();
    setIsGeneratingCopilot(true);
    setError(null);
    try {
      antdMessage.loading({
        content: `✨ 正在全网搜寻《${topicToUse}》爆款同款，去AI感改写并合成 3:4 原生实操卡...`,
        key: "copilot",
        duration: 0,
      });
      const newJob = await generateCopilotJob(topicToUse);
      setIsCopilotModalOpen(false);
      setCopilotTopic("");
      antdMessage.success({
        content: `🎉 爆款仿写完成！已为您自动生成《${newJob.title}》，请在真机预览中确认。`,
        key: "copilot",
        duration: 5,
      });
      await loadJobs();
      setSelectedJobId(newJob.id);
      applyJob(newJob);
      await loadAssets(newJob.id);
      setPreviewTab("phone");
    } catch (err: unknown) {
      const d = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      antdMessage.error({ content: d || "生成失败，请重试", key: "copilot", duration: 4 });
      setError(d || "智能搜同款生成失败");
    } finally {
      setIsGeneratingCopilot(false);
    }
  }

  useEffect(() => {
    void loadJobs();
    void loadAccounts();
  }, []);

  const scheduledDayjs: Dayjs | null = scheduledAt ? dayjs(scheduledAt) : null;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      <PageHeader
        eyebrow="XHS Publish"
        title="发布中心"
        description="预览草稿内容，配置发布参数后触发 Creator 发布。支持 AI 智能搜同款仿写与 1:1 真机效果确认。"
        action={
          <Space>
            <Button
              type="primary"
              style={{ background: "#722ed1", borderColor: "#722ed1", fontWeight: "bold" }}
              icon={<ThunderboltOutlined />}
              onClick={() => setIsCopilotModalOpen(true)}
            >
              ✨ AI 搜同款一键生成 (带预览)
            </Button>
            <Button
              icon={<KeyOutlined />}
              onClick={async () => {
                try {
                  const res = await launchBrowserLogin();
                  antdMessage.success(res.message);
                } catch {
                  antdMessage.info("请双击桌面的【小红书防封浏览器】进行扫码登录");
                }
              }}
            >
              🔑 打开防封浏览器扫码
            </Button>
            <Button icon={<ReloadOutlined />} onClick={loadJobs} loading={isLoading}>
              刷新
            </Button>
          </Space>
        }
      />

      {/* AI 搜同款生成 Modal */}
      <Modal
        title={
          <Space>
            <ThunderboltOutlined style={{ color: "#722ed1" }} />
            <span>AI 智能搜同款生成器 (爆款分析 + 去AI感仿写 + 3:4 实操卡)</span>
          </Space>
        }
        open={isCopilotModalOpen}
        onCancel={() => setIsCopilotModalOpen(false)}
        footer={null}
        destroyOnClose
      >
        <Paragraph type="secondary" style={{ fontSize: 13, marginBottom: 16 }}>
          输入你想要生成的赛道选题（如“AI工具”、“职场摸鱼”、“副业搞钱”），系统将自动搜寻小红书当前高赞同款结构，去 AI 感改写为真实第一人称种草文案，并合成 3:4 原生视觉图卡。生成后直接送入真机预览，确认无误后可一键防封全自动发布！
        </Paragraph>
        <Space direction="vertical" style={{ width: "100%" }} size={16}>
          <Input.Search
            placeholder="例如：AI生产力工具 / 搞钱副业 / 经方养生"
            enterButton="一键搜同款并生成"
            size="large"
            value={copilotTopic}
            onChange={(e) => setCopilotTopic(e.target.value)}
            loading={isGeneratingCopilot}
            onSearch={() => handleRunCopilot(copilotTopic)}
          />
          <div>
            <Text type="secondary" style={{ fontSize: 12 }}>⚡ 推荐热门同款灵感：</Text>
            <Space size={8} wrap style={{ marginTop: 8 }}>
              {["AI工具与生产力", "打工人避坑神器", "自媒体爆款写作", "零成本搞钱技能"].map((preset) => (
                <Tag
                  key={preset}
                  style={{ cursor: "pointer", padding: "4px 8px" }}
                  color="purple"
                  onClick={() => {
                    setCopilotTopic(preset);
                    void handleRunCopilot(preset);
                  }}
                >
                  {preset}
                </Tag>
              ))}
            </Space>
          </div>
        </Space>
      </Modal>

      {error && <Alert type="error" message={error} showIcon closable onClose={() => setError(null)} />}
      {message && <Alert type="success" message={message} showIcon closable onClose={() => setMessage(null)} />}

      {isLoading ? (
        <Card style={panelStyle} styles={{ body: cardBodyStyle }}>
          <div style={{ textAlign: "center", padding: 48 }}>
            <Spin size="large" />
            <Paragraph style={{ color: "#8c8c8c", marginTop: 16 }}>正在加载发布任务...</Paragraph>
          </div>
        </Card>
      ) : jobs.length === 0 ? (
        <Card style={panelStyle} styles={{ body: cardBodyStyle }}>
          <Empty
            image={<SendOutlined style={{ fontSize: 48, color: "#8c8c8c" }} />}
            imageStyle={{ height: 64 }}
            description={
              <div>
                <Text strong style={{ fontSize: 16 }}>暂无发布任务</Text>
                <br />
                <Text type="secondary">在草稿工坊中将草稿送入发布中心，或通过自动运营生成发布任务。</Text>
              </div>
            }
          />
        </Card>
      ) : (
        <Row gutter={16}>
          {/* Left: Job List */}
          <Col xs={24} lg={7}>
            <Card
              title={
                <Space>
                  <Text strong>发布任务</Text>
                  <Select
                    size="small"
                    value={statusFilter}
                    onChange={setStatusFilter}
                    style={{ width: 100 }}
                    options={[
                      { value: "all", label: "全部" },
                      ...Object.entries(STATUS_TAG_MAP).map(([key, val]) => ({ value: key, label: val.label })),
                    ]}
                  />
                </Space>
              }
              extra={<Tag>{filteredJobs.length} 个</Tag>}
              style={panelStyle}
              styles={{ body: { padding: 0 }, header: { borderBottom: "1px solid #303030" } }}
            >
              <List
                dataSource={filteredJobs}
                renderItem={(job) => (
                  <List.Item
                    onClick={() => handleSelect(job)}
                    style={{
                      cursor: "pointer",
                      padding: "12px 16px",
                      background: job.id === selectedJobId ? "rgba(22, 104, 220, 0.15)" : "transparent",
                      borderLeft: job.id === selectedJobId ? "3px solid #1668dc" : "3px solid transparent",
                      transition: "all 0.2s",
                    }}
                  >
                    <List.Item.Meta
                      title={<Text ellipsis style={{ maxWidth: "100%", color: "#e8e8e8" }}>{job.title || "未命名"}</Text>}
                      description={
                        <Space direction="vertical" size={4} style={{ width: "100%" }}>
                          <Space size={4} wrap>
                            {getStatusTag(job.status)}
                            <Tag>{job.publish_mode === "scheduled" ? "定时" : "即时"}</Tag>
                          </Space>
                          <Text type="secondary" style={{ fontSize: 11 }}>{formatShanghaiTime(job.created_at)}</Text>
                        </Space>
                      }
                    />
                  </List.Item>
                )}
                style={{ maxHeight: "calc(100vh - 260px)", overflowY: "auto" }}
              />
            </Card>
          </Col>

          {/* Right: Preview + Settings */}
          <Col xs={24} lg={17}>
            {!selectedJob ? (
              <Card style={panelStyle} styles={{ body: cardBodyStyle }}>
                <Empty description="请选择一个发布任务" />
              </Card>
            ) : (
              <Spin spinning={isDetailLoading}>
                <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                  {/* Toolbar */}
                  <Card style={panelStyle} styles={{ body: { padding: "12px 16px" } }}>
                    <Row justify="space-between" align="middle">
                      <Col>
                        <Title level={5} style={{ margin: 0 }}>#{selectedJob.id} {selectedJob.title || "未命名"}</Title>
                        <Space size={8} style={{ marginTop: 4 }}>
                          {getStatusTag(selectedJob.status)}
                          {selectedJob.publish_error && <Text type="danger" style={{ fontSize: 12 }}>{selectedJob.publish_error}</Text>}
                        </Space>
                      </Col>
                      <Col>
                        <Space wrap>
                          <Button icon={<SaveOutlined />} onClick={handleSave} loading={isSaving}>保存参数</Button>
                          <Popconfirm title="确定删除此发布任务？" onConfirm={handleDeleteJob}>
                            <Button danger icon={<DeleteOutlined />}>删除</Button>
                          </Popconfirm>
                          <Button
                            type="primary"
                            size="middle"
                            style={{ background: "#52c41a", borderColor: "#52c41a", fontWeight: "bold", boxShadow: "0 0 10px rgba(82, 196, 26, 0.4)" }}
                            icon={<RobotOutlined />}
                            onClick={handleMcpPublish}
                            loading={isMcpPublishing}
                          >
                            🚀 MCP 防封环境全自动发布 (免配Cookie)
                          </Button>
                          <Button
                            type="text"
                            icon={<SendOutlined />}
                            onClick={handlePublish}
                            loading={isPublishing}
                            disabled={!canPublish}
                            style={{ color: "#8c8c8c", fontSize: 12 }}
                          >
                            传统API发布 (需Cookie)
                          </Button>
                        </Space>
                      </Col>
                    </Row>
                  </Card>

                  {/* Compliance Guard Panel */}
                  <ComplianceGuardCard
                    title={selectedJob.title}
                    body={selectedJob.body}
                    compact={true}
                    onApplyCleaned={async (cleanedTitle, cleanedBody) => {
                      try {
                        const updated = await updatePublishJob(selectedJob.id, {
                          title: cleanedTitle,
                          body: cleanedBody,
                        });
                        setJobs((prev) => prev.map((j) => (j.id === updated.id ? updated : j)));
                      } catch (e) {
                        console.error("Failed to update sanitized job", e);
                      }
                    }}
                  />

                  <Row gutter={16}>
                    {/* Content Preview & Mobile Mockup */}
                    <Col xs={24} md={14}>
                      <Card
                        title={
                          <Space>
                            <Segmented
                              value={previewTab}
                              onChange={(val) => setPreviewTab(val as "phone" | "meta")}
                              options={[
                                { label: "📱 真机效果预览", value: "phone", icon: <MobileOutlined /> },
                                { label: "📄 排版与素材", value: "meta", icon: <EyeOutlined /> },
                              ]}
                            />
                          </Space>
                        }
                        style={panelStyle}
                        styles={{
                          body: {
                            ...cardBodyStyle,
                            display: previewTab === "phone" ? "flex" : "block",
                            justifyContent: "center",
                            background: previewTab === "phone" ? "#0f0f12" : undefined,
                          },
                          header: { borderBottom: "1px solid #303030" },
                        }}
                        extra={
                          previewTab === "phone" ? (
                            <Tag color="cyan">小红书真机视网膜渲染 (3:4)</Tag>
                          ) : (
                            <Text type="secondary" style={{ fontSize: 12 }}>内容修改请前往草稿工坊</Text>
                          )
                        }
                      >
                        {previewTab === "phone" ? (
                          <XhsMobilePreview
                            title={selectedJob.title || ""}
                            body={selectedJob.body || ""}
                            topics={parseTopics(topicsText)}
                            assets={assets}
                            authorName={
                              accounts.find((a) => a.id === selectedAccountId)?.nickname || "小红书创作者"
                            }
                          />
                        ) : (
                          <div>
                            <Title level={5} style={{ marginBottom: 8 }}>{selectedJob.title || "未填写标题"}</Title>
                            <Paragraph style={{ whiteSpace: "pre-wrap", color: "rgba(255,255,255,.65)", fontSize: 13, marginBottom: 16 }}>
                              {selectedJob.body || "暂无正文"}
                            </Paragraph>

                            {imageAssets.length > 0 && (
                              <div style={{ marginBottom: 12 }}>
                                <Text type="secondary" style={{ fontSize: 12, display: "block", marginBottom: 6 }}>
                                  <PictureOutlined /> 图片素材 ({imageAssets.length})
                                </Text>
                                <Image.PreviewGroup>
                                  <Space size={8} wrap>
                                    {imageAssets.map((asset) => (
                                      <Image
                                        key={asset.id}
                                        src={asset.file_path}
                                        width={80}
                                        height={80}
                                        style={{ objectFit: "cover", borderRadius: 6 }}
                                        referrerPolicy="no-referrer"
                                        fallback="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iODAiIGhlaWdodD0iODAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHJlY3Qgd2lkdGg9IjgwIiBoZWlnaHQ9IjgwIiBmaWxsPSIjMjYyNjI2Ii8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGRvbWluYW50LWJhc2VsaW5lPSJtaWRkbGUiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGZpbGw9IiM4YzhjOGMiIGZvbnQtc2l6ZT0iMTIiPuWbvueJhzwvdGV4dD48L3N2Zz4="
                                      />
                                    ))}
                                  </Space>
                                </Image.PreviewGroup>
                              </div>
                            )}

                            {videoAssets.length > 0 && (
                              <div style={{ marginBottom: 12 }}>
                                <Text type="secondary" style={{ fontSize: 12, display: "block", marginBottom: 6 }}>
                                  <PlayCircleOutlined /> 视频素材 ({videoAssets.length})
                                </Text>
                                <Space wrap>
                                  {videoAssets.map((asset) => (
                                    <Button key={asset.id} type="link" icon={<PlayCircleOutlined />} href={asset.file_path} target="_blank" rel="noreferrer" size="small">
                                      查看视频
                                    </Button>
                                  ))}
                                </Space>
                              </div>
                            )}

                            {!hasAnyAsset && <Text type="secondary">暂无素材</Text>}

                            {selectedJob.publish_options?.draft_tags && Array.isArray(selectedJob.publish_options.draft_tags) && selectedJob.publish_options.draft_tags.length > 0 && (
                              <div style={{ marginTop: 12 }}>
                                <Space size={[4, 4]} wrap>
                                  {(selectedJob.publish_options.draft_tags as Array<{name?: string}>).map((t, i) => (
                                    <Tag key={i} color="blue">#{t.name || ""}</Tag>
                                  ))}
                                </Space>
                              </div>
                            )}
                          </div>
                        )}
                      </Card>
                    </Col>

                    {/* Right side: settings + checks */}
                    <Col xs={24} md={10}>
                      {/* Publish Settings */}
                      <Card
                        title={<Space><CalendarOutlined /><span>发布参数</span></Space>}
                        style={{ ...panelStyle, marginBottom: 16 }}
                        styles={{ body: cardBodyStyle, header: { borderBottom: "1px solid #303030" } }}
                      >
                        <Form layout="vertical" size="small">
                          <Form.Item label="发布账号" required>
                            <Select
                              value={selectedAccountId}
                              onChange={(val) => setSelectedAccountId(val)}
                              placeholder="选择 Creator 账号"
                              style={{ width: "100%" }}
                              options={creatorAccounts.map((a) => ({ value: a.id, label: a.nickname || `账号 #${a.id}` }))}
                              notFoundContent="暂无 Creator 账号"
                            />
                          </Form.Item>
                          <Form.Item label="地点">
                            <Input value={location} onChange={(e) => setLocation(e.target.value)} placeholder="可不填" />
                          </Form.Item>
                          <Row gutter={8}>
                            <Col span={12}>
                              <Form.Item label="可见性">
                                <Select
                                  value={privacyChoice}
                                  onChange={(val) => setPrivacyChoice(val)}
                                  options={[
                                    { value: "public", label: "公开" },
                                    { value: "private", label: "私密" },
                                  ]}
                                />
                              </Form.Item>
                            </Col>
                            <Col span={12}>
                              <Form.Item label="发布模式">
                                <Select
                                  value={publishMode}
                                  onChange={(val) => setPublishMode(val)}
                                  options={[
                                    { value: "immediate", label: "立即发布" },
                                    { value: "scheduled", label: "定时发布" },
                                  ]}
                                />
                              </Form.Item>
                            </Col>
                          </Row>
                          {publishMode === "scheduled" && (
                            <Form.Item label="定时时间">
                              <DatePicker
                                showTime
                                value={scheduledDayjs}
                                onChange={(val: Dayjs | null) => setScheduledAt(val ? val.format("YYYY-MM-DDTHH:mm") : "")}
                                style={{ width: "100%" }}
                                format="YYYY-MM-DD HH:mm"
                              />
                            </Form.Item>
                          )}
                        </Form>
                      </Card>

                      {/* Status Checks */}
                      <Card
                        title={
                          <Space>
                            {readyChecks.every((c) => c.ok) ? <CheckCircleOutlined style={{ color: "#52c41a" }} /> : <ExclamationCircleOutlined style={{ color: "#faad14" }} />}
                            <span>发布校验</span>
                          </Space>
                        }
                        style={panelStyle}
                        styles={{ body: cardBodyStyle, header: { borderBottom: "1px solid #303030" } }}
                      >
                        <List
                          size="small"
                          dataSource={readyChecks}
                          renderItem={(check) => (
                            <List.Item style={{ padding: "4px 0", border: "none" }}>
                              <Space>
                                {check.ok ? <CheckCircleOutlined style={{ color: "#52c41a" }} /> : <ExclamationCircleOutlined style={{ color: "#ff4d4f" }} />}
                                <Text style={{ color: check.ok ? "#8c8c8c" : "#ff4d4f", fontSize: 13 }}>{check.label}</Text>
                              </Space>
                            </List.Item>
                          )}
                        />
                        {selectedJob.external_note_id && (
                          <div style={{ marginTop: 8 }}>
                            <Text type="secondary" style={{ fontSize: 12 }}>已发布笔记：{selectedJob.external_note_id}</Text>
                          </div>
                        )}
                      </Card>
                    </Col>
                  </Row>
                </div>
              </Spin>
            )}
          </Col>
        </Row>
      )}
    </div>
  );
}
