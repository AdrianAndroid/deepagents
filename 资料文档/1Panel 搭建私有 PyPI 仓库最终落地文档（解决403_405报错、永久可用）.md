# 1Panel 搭建私有 PyPI 仓库最终落地文档（解决403/405报错、永久可用）

## 一、环境与最终定型信息

- 服务器：2核2G 云服务器

- 管理工具：1Panel

- 镜像：**pypiserver/pypiserver:latest**（重点：不是默认 library/pypiserver）

- 端口方案：容器内部固定 8080，主机映射 **40001**（规避8080端口占用）

- 存储方案：持久化挂载，包数据永不丢失

- 鉴权方案：废弃环境变量鉴权，使用官方标准 htpasswd 文件鉴权（唯一支持上传\+下载鉴权的方式）

- 解决所有报错：403权限禁止、405方法不允许、镜像拉取520/403失败、镜像不存在报错

## 二、初始容器正确配置（新建容器标准模板）

若后续重装，严格按照此配置，一次成功

### 1\. 基础配置

- 容器名称：pypi\-server

- 镜像：pypiserver/pypiserver:latest

- 强制拉取镜像：**不勾选**（规避1Panel镜像源520报错）

- 重启策略：**一直重启**（开机自启、异常自动恢复）

### 2\. 端口映射（必对）

- 服务器端口：40001

- 容器端口：8080（固定不可改）

- 协议：TCP

### 3\. 数据持久化挂载（必配）

- 主机目录：/opt/pypiserver/packages

- 容器目录：/data/packages

- 权限：读写

### 4\. 资源配置（2核2G服务器固定）

- CPU权重：1024（默认不变）

- CPU限制：0（不限制）

- 内存限制：0（不限制）

### 5\. 初始错误配置（禁止使用！踩坑记录）

❌ 废弃配置：环境变量 `PYPISERVER_AUTH=admin:123456`

问题：仅网页浏览可登录，**所有twine上传请求直接403禁止访问**，完全无法用于包上传，属于无效生产配置。

## 三、存量容器无损改造方案（不删容器、保留所有数据）

针对已经创建好的容器，原地修复上传403/405报错，无需重建

### 步骤1：服务器终端生成标准鉴权文件（核心）

```bash
# 安装密码工具
apt update && apt install apache2-utils -y

# 生成htpasswd鉴权文件（用户名admin，密码123456，输入两次确认）
htpasswd -c /opt/pypiserver/packages/.htpasswd admin
```

### 步骤2：1Panel编辑容器修改配置

容器 → pypi\-server → 编辑

1. **清空所有环境变量**：删除原有的 PYPISERVER\_AUTH 配置，彻底清空

2. **填写Command启动参数（关键）**：
        `-P /data/packages/.htpasswd -a download,update /data/packages`

3. 参数释义：开启登录鉴权 \+ 允许下载、上传权限 \+ 指定包存储目录

4. 保存配置，**重启容器**

## 四、最终正确使用命令（唯一可用版本）

### 1\. Twine 上传 WHL 包（解决403/405报错）

✅ 正确地址：根路径 `http://IP:40001/`

❌ 错误地址：带 /simple、/upload 后缀（会405方法不允许）

```bash
twine upload --repository-url http://8.152.204.58:40001/ -u admin -p 123456 你的包名.whl
```

### 2\. Pip 下载/安装私有包

✅ 正确地址：必须带 /simple 后缀

```bash
pip install 包名 -i http://admin:123456@8.152.204.58:40001/simple/ --trusted-host 8.152.204.58
```

## 五、核心地址对照表（永久记忆）

|操作场景|正确地址|错误后果|
|---|---|---|
|twine 上传包|http://IP:40001/|加后缀405报错|
|pip 安装包/网页浏览|http://IP:40001/simple/|无法索引包列表|

## 六、所有报错终极复盘（避坑大全）

1. **镜像 not found**：错误使用 pypiserver:latest，正确为 pypiserver/pypiserver:latest

2. **镜像拉取403**：DaoCloud加速源封禁匿名访问

3. **镜像拉取520**：1Panel自带docker\.1panel\.live节点宕机

4. **上传405 Method Not Allowed**：上传地址带 /simple 或 /upload 后缀

5. **上传403 Forbidden**：使用环境变量鉴权，不支持上传操作，必须改用htpasswd文件鉴权\+启动参数开启update权限

## 七、落地自检清单（每次操作核对）

- \[√\] 端口映射：40001:8080 TCP

- \[√\] 持久化挂载目录正确

- \[√\] 容器重启策略：一直重启

- \[√\] 无任何 PYPISERVER\_AUTH 环境变量

- \[√\] Command 启动参数完整无误

- \[√\] 服务器存在 \.htpasswd 鉴权文件

- \[√\] 防火墙/安全组放行40001端口

> （注：部分内容可能由 AI 生成）
