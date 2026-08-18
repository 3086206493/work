-- ============================================================
-- 可选：初始化 aj_report 演示库
-- ============================================================
-- 如果你的本地 MySQL 还没有 aj_report 库，或者想用一份示例报表数据
-- 来体验「查询 + 导出」，执行本脚本即可：
--
--   mysql -u root -p123456 < scripts/setup_aj_report.sql
--
-- 说明：
--   * 本工具本身不创建库/表，它直接连接已存在的 aj_report 库。
--   * 如果你已有自己的 aj_report 报表库，可跳过本脚本，直接运行工具。
--   * 脚本幂等：表与数据已存在时不会重复插入（INSERT 带 IGNORE）。
-- ============================================================

CREATE DATABASE IF NOT EXISTS aj_report
  DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;

USE aj_report;

-- 每日运营报表事实表（含数值列，便于导出 HTML 柱状图）
DROP TABLE IF EXISTS report_daily;
CREATE TABLE report_daily (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  report_date DATE        NOT NULL,
  region      VARCHAR(50) NOT NULL COMMENT '大区',
  channel     VARCHAR(50) NOT NULL COMMENT '渠道',
  visits      INT         NOT NULL DEFAULT 0 COMMENT '访问量',
  orders      INT         NOT NULL DEFAULT 0 COMMENT '下单量',
  revenue     DECIMAL(12,2) NOT NULL DEFAULT 0.00 COMMENT '销售额'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT IGNORE INTO report_daily (id, report_date, region, channel, visits, orders, revenue) VALUES
  (1,  '2026-01-31', '华东', '小程序',  18230, 2140, 386520.00),
  (2,  '2026-01-31', '华东', 'APP',    15420, 1890, 342180.00),
  (3,  '2026-01-31', '华南', '小程序',  12980, 1530, 263560.00),
  (4,  '2026-01-31', '华南', 'APP',    10240, 1190, 201230.00),
  (5,  '2026-01-31', '华北', '小程序',  14560, 1720, 297840.00),
  (6,  '2026-01-31', '华北', 'APP',     9870, 1080, 182060.00),
  (7,  '2026-02-28', '华东', '小程序',  21030, 2580, 471120.00),
  (8,  '2026-02-28', '华东', 'APP',    17640, 2210, 402030.00),
  (9,  '2026-02-28', '华南', '小程序',  14120, 1680, 289140.00),
  (10, '2026-02-28', '华南', 'APP',    11360, 1320, 223980.00),
  (11, '2026-02-28', '华北', '小程序',  15890, 1900, 331650.00),
  (12, '2026-02-28', '华北', 'APP',    11020, 1260, 213840.00);
