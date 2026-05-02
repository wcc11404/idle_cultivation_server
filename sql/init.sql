-- 数据库初始化总入口
-- 说明：按子系统拆分到 sql/schema/*.sql，这里只负责控制执行顺序。

\ir schema/00_extensions_and_functions.sql
\ir schema/10_accounts_and_player.sql
\ir schema/20_mail.sql
\ir schema/30_seed_test_accounts.sql
\ir schema/40_ops.sql
