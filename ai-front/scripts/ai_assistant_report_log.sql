/*
 Navicat Premium Data Transfer

 Source Server         : docker pg
 Source Server Type    : PostgreSQL
 Source Server Version : 160009 (160009)
 Source Host           : localhost:5432
 Source Catalog        : fba
 Source Schema         : public

 Target Server Type    : PostgreSQL
 Target Server Version : 160009 (160009)
 File Encoding         : 65001

 Date: 11/07/2025 16:48:56
*/


-- ----------------------------
-- Table structure for ai_assistant_report_log
-- ----------------------------
DROP TABLE IF EXISTS "public"."ai_assistant_report_log";
CREATE TABLE "public"."ai_assistant_report_log" (
  "id" int4 NOT NULL DEFAULT nextval('ai_assistant_report_log_id_seq'::regclass),
  "assistant_id" varchar(36) COLLATE "pg_catalog"."default" NOT NULL,
  "member_id" int4 NOT NULL,
  "sql_data" text COLLATE "pg_catalog"."default",
  "prompt_data" text COLLATE "pg_catalog"."default",
  "input_prompt" text COLLATE "pg_catalog"."default",
  "report_status" bool NOT NULL DEFAULT true,
  "report_score" float8 NOT NULL,
  "report_result" text COLLATE "pg_catalog"."default",
  "report_table" text COLLATE "pg_catalog"."default",
  "report_document" text COLLATE "pg_catalog"."default",
  "create_time" timestamp(6) NOT NULL DEFAULT now(),
  "update_time" timestamp(6) NOT NULL DEFAULT now()
)
;
COMMENT ON COLUMN "public"."ai_assistant_report_log"."id" IS '报告ID';
COMMENT ON COLUMN "public"."ai_assistant_report_log"."assistant_id" IS 'AI助手ID';
COMMENT ON COLUMN "public"."ai_assistant_report_log"."member_id" IS '用户ID';
COMMENT ON COLUMN "public"."ai_assistant_report_log"."sql_data" IS 'SQL查询数据，JSON格式';
COMMENT ON COLUMN "public"."ai_assistant_report_log"."prompt_data" IS '提示词数据，JSON格式';
COMMENT ON COLUMN "public"."ai_assistant_report_log"."input_prompt" IS '输入提示词';
COMMENT ON COLUMN "public"."ai_assistant_report_log"."report_status" IS '报告状态';
COMMENT ON COLUMN "public"."ai_assistant_report_log"."report_score" IS '报告评分';
COMMENT ON COLUMN "public"."ai_assistant_report_log"."report_result" IS '报告结果';
COMMENT ON COLUMN "public"."ai_assistant_report_log"."report_table" IS '报告表格数据，JSON格式';
COMMENT ON COLUMN "public"."ai_assistant_report_log"."report_document" IS '报告文档';
COMMENT ON COLUMN "public"."ai_assistant_report_log"."create_time" IS '创建时间';
COMMENT ON COLUMN "public"."ai_assistant_report_log"."update_time" IS '更新时间';
COMMENT ON TABLE "public"."ai_assistant_report_log" IS 'AI助手报告记录表';

-- ----------------------------
-- Records of ai_assistant_report_log
-- ----------------------------

-- ----------------------------
-- Indexes structure for table ai_assistant_report_log
-- ----------------------------
CREATE INDEX "ix_ai_assistant_report_log_id" ON "public"."ai_assistant_report_log" USING btree (
  "id" "pg_catalog"."int4_ops" ASC NULLS LAST
);
CREATE INDEX "ix_ai_assistant_report_log_member_id" ON "public"."ai_assistant_report_log" USING btree (
  "member_id" "pg_catalog"."int4_ops" ASC NULLS LAST
);

-- ----------------------------
-- Primary Key structure for table ai_assistant_report_log
-- ----------------------------
ALTER TABLE "public"."ai_assistant_report_log" ADD CONSTRAINT "ai_assistant_report_log_pkey" PRIMARY KEY ("id");
