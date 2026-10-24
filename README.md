# Shadowrocket YouTube Web

一个针对 **YouTube 网页版** 的实验性 Shadowrocket 模组，记录一次 macOS Chrome 去广告修复及其验证结果。通过 HTTPS 解密与原生 Body Rewrite 改写播放器广告字段，不依赖浏览器扩展或远程 JavaScript。

**公开模组不含证书、私钥或口令。安装前必须在自己的设备上配置并信任自己的 CA。** 本项目不提供共享 CA，也不保证覆盖所有广告形式。

## 下载

- [模组原始文件](https://raw.githubusercontent.com/Apo-asph/shadowrocket-youtube-web/main/YouTube-Web.sgmodule)
- [查看模组](YouTube-Web.sgmodule)

在 Shadowrocket 的「配置 → 模组」中添加原始文件链接，或下载后作为本地模组导入。先完成下面的证书配置，再启用模组。

## 安装与配置

1. 备份当前配置，停用其他 YouTube 去广告模组，避免重写冲突。
2. 在当前配置的「HTTPS 解密 → 证书」中配置自己的 CA，并按 Shadowrocket 提示安装到本机、在系统中设置信任。证书私钥及其口令应只保存在自己的设备上；包含这些内容的配置或模组不要上传公开仓库或开启云同步。
3. 启用本模组，然后重新应用当前配置（Use Config）。本模组设置 `enable = true` 和 `h2 = true`，并将有效解密域名限定为 `www.youtube.com,m.youtube.com`。
4. 确认这两个域名的 HTTPS 连接实际使用你自己的 CA，且其他网站仍使用原始网站证书，再重新加载 YouTube 页面测试播放。

`hostname` 使用替换语义，不含 `%APPEND%`：它会覆盖主配置已有的解密域名列表。这是为了限定本模组的解密范围，也意味着其他需要 HTTPS 解密的功能可能受影响。多个模组并用时必须检查合并后的实际效果。

证书设置按设备和系统版本可能有所不同。若浏览器出现证书警告，停用模组，检查 CA 安装和信任状态；不要通过忽略证书验证来完成安装。公开版本只发布过滤规则，未在一台全新设备上独立验证完整安装流程。

## 工作方式

| 部分 | 行为 |
| --- | --- |
| Rule | 拒绝两个目标域名的 UDP 流量，促使请求使用可处理的 TCP 连接 |
| MITM | 对两个目标域名启用 HTTPS 解密和 HTTP/2 支持 |
| Body Rewrite | 在匹配的网页或接口响应中，将 `adPlacements`、`playerAds`、`adSlots` 重命名为 `srDisabled…` 字段 |

匹配范围是首页、`/watch`，以及 `/youtubei/v1/player`、`next`、`browse` 接口及其子路径（包含 `player/ad_break`）。不重写播放器 JavaScript、视频媒体流或第三方网站。字段替换是原生文本替换，不是结构化 JSON 删除，也不会过滤所有形式的广告数据。

模组适用于网页响应。本项目没有实现 YouTube App 的 protobuf 处理，也没有验证 App、Shorts、嵌入式播放器、直播和全部广告形式。视频作者直接录入内容的赞助片段不在处理范围内。

## 已验证结果

2026-10-24，macOS、Shadowrocket 2.2.92（3445）、Chrome：

- 原有规则未匹配此次捕获的网页广告请求；当时的 HTTPS 连接也未实际解密。
- 修复后，连接证书确认 YouTube HTTPS 解密生效；浏览器网络面板确认网页响应中的 `adPlacements` 和 `adSlots` 已被替换。
- 同一视频页面两次重新加载后直接正常播放，未出现此前观察到的广告。
- 恢复主配置的临时修改、重新应用配置后，模组提供的解密仍有效；检查的一个非目标域名保持原始网站证书。

以上是单台设备、同一视频的有限实测，不能证明长期有效或适用于所有账号、地区和广告实验。最后一次无广告时间不确定，不能据此确定最初失效时间或归因于某次 YouTube 更新。

实测安装将 CA 材料保存在本机专用模组中；公开文件去除了这些材料，要求使用者自行配置 CA。未发布个人主配置、节点、日志、浏览器响应、证书和私钥。

## 排查与回退

设置页的开关可能只反映主配置，模组还会覆盖对应字段；开关显示不能单独证明实际解密状态。本次排查曾临时打开主配置开关，最终恢复主配置后仍有效，因此没有证据表明必须永久修改主配置总开关。

排查时依次确认：

1. 模组已启用，当前配置已重新应用。
2. YouTube 的实际连接证书由自己配置的 CA 签发，浏览器没有证书错误。
3. 网络响应中能找到 `srDisabledAdPlacements` 或 `srDisabledAdSlots`。响应原本没有广告字段时，没有匹配结果也不能单独判断失败。
4. 检查新加载的视频和后续页面切换。YouTube 响应格式变化可能使这些规则失效。

回退时停用本模组、重新应用配置，恢复自己备份的解密设置。若 CA 仅为本模组创建且已不再使用，再撤销系统信任并移除该证书。停用模组后主配置原有的解密域名设置会重新生效，应一并核对。

提交 Issue 时请提供软件版本、广告出现位置和去除敏感信息的规则匹配情况；不要上传证书、口令、Cookie、完整 HAR 或个人代理配置。

## 本地检查

无需安装依赖，运行：

```sh
python3 tests/validate.py
```

检查 URL 匹配边界、示例 JSON 经替换后的可解析性和公开文件中的敏感材料。这是静态检查，不模拟 Shadowrocket 的运行时，也不代替真实播放测试。

## 参考与许可

- [Shadowrocket 发布频道](https://t.me/ShadowrocketNews)：原生 Body Rewrite 功能说明。
- [LOWERTOP/Shadowrocket 使用指南](https://github.com/LOWERTOP/Shadowrocket)：模组、MITM 和配置语法参考。

本仓库没有打包原有第三方去广告脚本。仓库文件使用 [MIT License](LICENSE)。
