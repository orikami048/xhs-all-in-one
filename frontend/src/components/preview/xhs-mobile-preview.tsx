import {
  HeartFilled,
  HeartOutlined,
  LeftOutlined,
  MessageOutlined,
  SearchOutlined,
  ShareAltOutlined,
  StarFilled,
  StarOutlined,
} from "@ant-design/icons";
import { Avatar, Carousel, Tag, Typography } from "antd";
import React, { useState } from "react";
import type { PublishAsset } from "../../types";

const { Text, Title, Paragraph } = Typography;

interface XhsMobilePreviewProps {
  title: string;
  body: string;
  topics?: string[];
  assets?: PublishAsset[];
  authorName?: string;
  avatarUrl?: string;
}

export function XhsMobilePreview({
  title,
  body,
  topics = [],
  assets = [],
  authorName = "AI 内容实验室",
  avatarUrl,
}: XhsMobilePreviewProps) {
  const [currentSlide, setCurrentSlide] = useState(0);
  const [liked, setLiked] = useState(false);
  const [starred, setStarred] = useState(false);

  const imageAssets = assets.filter((a) => a.asset_type === "image");
  const displayTitle = title.trim() || "待填写的爆款小红书标题";
  const displayBody = body.trim() || "这里是笔记正文预览。真实第一人称种草叙事，去 AI 感白描排版，让你的内容直击痛点并引发讨论...";

  return (
    <div
      style={{
        width: 360,
        height: 720,
        background: "#000000",
        borderRadius: 44,
        padding: "12px 10px",
        boxShadow: "0 25px 60px rgba(0,0,0,0.6), 0 0 0 3px #333, 0 0 0 6px #1a1a1a",
        display: "flex",
        flexDirection: "column",
        position: "relative",
        margin: "0 auto",
        userSelect: "none",
        border: "1px solid #444",
      }}
    >
      {/* 手机内屏 */}
      <div
        style={{
          flex: 1,
          background: "#ffffff",
          borderRadius: 34,
          overflow: "hidden",
          display: "flex",
          flexDirection: "column",
          color: "#333333",
          position: "relative",
        }}
      >
        {/* 顶部状态栏与灵动岛 */}
        <div
          style={{
            height: 38,
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "0 18px",
            fontSize: 12,
            fontWeight: 600,
            color: "#111",
            zIndex: 10,
            background: "rgba(255,255,255,0.9)",
          }}
        >
          <span>9:41</span>
          {/* 灵动岛胶囊 */}
          <div
            style={{
              width: 90,
              height: 20,
              background: "#000",
              borderRadius: 20,
              margin: "0 auto",
            }}
          />
          <span style={{ fontSize: 11 }}>5G 100%</span>
        </div>

        {/* 小红书 App 顶栏导航 */}
        <div
          style={{
            height: 40,
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "0 14px",
            borderBottom: "1px solid #f0f0f0",
            background: "#fff",
            zIndex: 9,
          }}
        >
          <LeftOutlined style={{ fontSize: 16, color: "#333", cursor: "pointer" }} />
          <div style={{ display: "flex", gap: 16, fontSize: 14, fontWeight: 500 }}>
            <span style={{ color: "#999" }}>关注</span>
            <span style={{ color: "#ff2442", fontWeight: 600, borderBottom: "2px solid #ff2442", paddingBottom: 2 }}>发现</span>
            <span style={{ color: "#999" }}>广州</span>
          </div>
          <div style={{ display: "flex", gap: 12, color: "#333", fontSize: 16 }}>
            <SearchOutlined />
            <ShareAltOutlined />
          </div>
        </div>

        {/* 可滚动笔记内容区 */}
        <div
          style={{
            flex: 1,
            overflowY: "auto",
            display: "flex",
            flexDirection: "column",
          }}
        >
          {/* 3:4 比例图片轮播区 */}
          <div
            style={{
              width: "100%",
              aspectRatio: "3 / 4",
              background: "#f7f7f7",
              position: "relative",
              overflow: "hidden",
            }}
          >
            {imageAssets.length > 0 ? (
              <>
                <Carousel
                  dots={false}
                  afterChange={(current) => setCurrentSlide(current)}
                  style={{ width: "100%", height: "100%" }}
                >
                  {imageAssets.map((asset, index) => (
                    <div key={asset.id || index} style={{ width: "100%", height: "100%" }}>
                      <img
                        src={asset.file_path}
                        alt={`Preview ${index + 1}`}
                        style={{
                          width: "100%",
                          height: "100%",
                          objectFit: "cover",
                          display: "block",
                        }}
                      />
                    </div>
                  ))}
                </Carousel>
                {/* 右上角指示器 1/4 */}
                <div
                  style={{
                    position: "absolute",
                    top: 12,
                    right: 12,
                    background: "rgba(0,0,0,0.55)",
                    color: "#fff",
                    padding: "2px 8px",
                    borderRadius: 12,
                    fontSize: 11,
                    fontWeight: 600,
                  }}
                >
                  {currentSlide + 1}/{imageAssets.length}
                </div>
              </>
            ) : (
              /* 无素材时的标准 3:4 封面占位符 */
              <div
                style={{
                  width: "100%",
                  height: "100%",
                  background: "linear-gradient(145deg, #fff0f2 0%, #fee6ea 100%)",
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  justifyContent: "center",
                  padding: 24,
                  textAlign: "center",
                  color: "#ff2442",
                }}
              >
                <div
                  style={{
                    fontSize: 11,
                    fontWeight: 700,
                    letterSpacing: 2,
                    textTransform: "uppercase",
                    marginBottom: 12,
                    background: "rgba(255,36,66,0.1)",
                    padding: "4px 10px",
                    borderRadius: 20,
                  }}
                >
                  3:4 高清封面规范
                </div>
                <div
                  style={{
                    fontSize: 18,
                    fontWeight: 800,
                    color: "#222",
                    lineHeight: 1.4,
                    maxWidth: 240,
                    marginBottom: 16,
                  }}
                >
                  {displayTitle}
                </div>
                <div style={{ fontSize: 11, color: "#888" }}>
                  建议上传 1200 × 1600 高清竖图
                </div>
              </div>
            )}
          </div>

          {/* 作者栏 */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              padding: "10px 14px",
              borderBottom: "1px solid #f8f8f8",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <Avatar
                src={avatarUrl}
                size={34}
                style={{ background: "#ff2442", fontWeight: 700 }}
              >
                {authorName[0] || "红"}
              </Avatar>
              <div style={{ display: "flex", flexDirection: "column" }}>
                <span style={{ fontSize: 13, fontWeight: 600, color: "#222" }}>
                  {authorName}
                </span>
                <span style={{ fontSize: 10, color: "#999" }}>今天 12:00 · 广东</span>
              </div>
            </div>
            <button
              style={{
                border: "1px solid #ff2442",
                color: "#ff2442",
                background: "transparent",
                borderRadius: 16,
                padding: "3px 12px",
                fontSize: 12,
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              关注
            </button>
          </div>

          {/* 笔记标题与正文 */}
          <div style={{ padding: "12px 14px", flex: 1 }}>
            <Title
              level={5}
              style={{
                fontSize: 16,
                fontWeight: 700,
                color: "#111",
                marginBottom: 8,
                lineHeight: 1.4,
              }}
            >
              {displayTitle}
            </Title>

            <Paragraph
              style={{
                fontSize: 13,
                color: "#333",
                lineHeight: 1.6,
                whiteSpace: "pre-wrap",
                marginBottom: 12,
              }}
            >
              {displayBody}
            </Paragraph>

            {/* 话题标签 */}
            {topics.length > 0 && (
              <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 12 }}>
                {topics.map((tag, idx) => (
                  <span
                    key={idx}
                    style={{
                      color: "#13386c",
                      fontSize: 13,
                      fontWeight: 500,
                      cursor: "pointer",
                    }}
                  >
                    #{tag.replace(/^#/, "")}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* 底部互动操作栏 */}
        <div
          style={{
            height: 48,
            borderTop: "1px solid #f0f0f0",
            background: "#fff",
            display: "flex",
            alignItems: "center",
            padding: "0 14px",
            gap: 14,
            zIndex: 10,
          }}
        >
          {/* 仿真输入框 */}
          <div
            style={{
              flex: 1,
              background: "#f5f5f5",
              borderRadius: 20,
              padding: "6px 12px",
              fontSize: 12,
              color: "#999",
            }}
          >
            说点什么...
          </div>
          {/* 点赞 */}
          <div
            onClick={() => setLiked(!liked)}
            style={{ display: "flex", alignItems: "center", gap: 3, cursor: "pointer", fontSize: 13, color: liked ? "#ff2442" : "#333" }}
          >
            {liked ? <HeartFilled style={{ fontSize: 18, color: "#ff2442" }} /> : <HeartOutlined style={{ fontSize: 18 }} />}
            <span style={{ fontSize: 11, fontWeight: 600 }}>{liked ? "1.2k" : "1.1k"}</span>
          </div>
          {/* 收藏 */}
          <div
            onClick={() => setStarred(!starred)}
            style={{ display: "flex", alignItems: "center", gap: 3, cursor: "pointer", fontSize: 13, color: starred ? "#ffb800" : "#333" }}
          >
            {starred ? <StarFilled style={{ fontSize: 18, color: "#ffb800" }} /> : <StarOutlined style={{ fontSize: 18 }} />}
            <span style={{ fontSize: 11, fontWeight: 600 }}>{starred ? "889" : "888"}</span>
          </div>
          {/* 评论 */}
          <div style={{ display: "flex", alignItems: "center", gap: 3, fontSize: 13, color: "#333" }}>
            <MessageOutlined style={{ fontSize: 18 }} />
            <span style={{ fontSize: 11, fontWeight: 600 }}>168</span>
          </div>
        </div>
      </div>
    </div>
  );
}
