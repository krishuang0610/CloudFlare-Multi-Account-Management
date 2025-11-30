<img width="1024" height="511" alt="image" src="https://github.com/user-attachments/assets/d38f0251-34b6-4113-bbf8-f1287a1ab18f" />有些时候管理的CloudFlare 多帐户比较多，查找某一个域名太麻烦，所以开发这个小工具，这个工具完全由AI开发~😅
<img width="1024" height="511" alt="image" src="https://github.com/user-attachments/assets/cf8ad409-c3d5-467e-9e81-d011705cb447" />
<img width="1024" height="508" alt="image" src="https://github.com/user-attachments/assets/490ee272-c645-4569-928e-c40ce95b902f" />


## 使用方法

### 1. 自动加载 Account ID
- 登录账号后，系统会自动从 Cloudflare API 获取该账号有权限访问的所有 Account ID
- 下拉菜单会显示所有可用的 Account ID 及其名称

### 2. 切换 Account ID
1. 点击 "Account ID:" 后面的下拉菜单
2. 选择要切换的 Account ID
3. 系统会自动刷新域名列表，显示该 Account ID 下的所有域名

### 3. 查看所有账号
- 下拉菜单的第一个选项是 **"所有账号"**
- 选择此选项可以查看当前 API Token 有权限访问的所有域名（不限 Account ID）

## 下拉菜单选项格式

```
所有账号
账号名称 (12345678...)
账号名称2 (87654321...)
```

- **所有账号**：不指定 Account ID，显示所有域名
- **账号名称 (ID前缀...)**：显示账号名称和 Account ID 的前8位

## 使用场景

### 场景1：管理多个 Cloudflare 账号
如果您的 API Token 有权限访问多个 Account，可以通过下拉菜单快速切换：
1. 选择 "所有账号" - 查看所有域名
2. 选择特定 Account ID - 只查看该账号下的域名

### 场景2：批量操作特定账号的域名
1. 从下拉菜单选择目标 Account ID
2. 域名列表只显示该账号的域名
3. 执行批量添加、修改等操作

### 场景3：快速筛选域名
- 当您管理大量域名时
- 通过 Account ID 筛选可以快速定位到特定账号的域名

## 技术说明

### API 调用
- 使用 Cloudflare API `/accounts` 端点获取账号列表
- 使用 `/zones?account.id=xxx` 参数筛选域名

### 数据来源
1. **API 获取成功**：显示 API 返回的所有 Account ID
2. **API 获取失败**：使用配置文件中保存的 Account ID
3. **无 Account ID**：只显示"所有账号"选项

### 刷新机制
- 切换账号时自动加载 Account ID 列表
- 点击"刷新"按钮时使用当前选择的 Account ID
- 切换 Account ID 时自动刷新域名列表

## 注意事项

1. **API Token 权限**
   - 确保您的 API Token 有权限访问要查询的 Account
   - 没有权限的 Account 不会显示在列表中

2. **账号配置中的 Account ID**
   - 配置文件中保存的 Account ID 作为后备选项
   - 如果 API 调用失败，会使用配置中的 Account ID

3. **"所有账号"选项**
   - 选择此选项时，Account ID 参数为空
   - 会返回 API Token 有权限访问的所有域名
   - 可能跨越多个 Account

4. **性能考虑**
   - 切换 Account ID 会重新加载域名列表
   - 大量域名可能需要一些时间

## 快捷操作

- **快速切换**：直接点击下拉菜单选择
- **刷新当前账号**：点击"刷新"按钮
- **重新加载列表**：切换账号后自动刷新

## 与其他功能的配合

### 添加域名
- 添加域名时会使用当前选择的 Account ID
- 确保选择了正确的 Account ID

### 批量操作
- 批量添加域名会添加到当前选择的 Account ID
- 批量修改 DNS 记录只影响当前 Account ID 下的域名

### 导出功能
- 导出域名时只导出当前 Account ID 筛选后的域名列表
- 选择"所有账号"可导出全部域名

## 示例流程

### 示例1：查看特定账号的域名
```
1. 登录 Cloudflare 账号
2. 点击 Account ID 下拉菜单
3. 选择 "生产环境账号 (abcd1234...)"
4. 查看该账号下的所有域名
```

### 示例2：批量添加域名到指定账号
```
1. 从 Account ID 下拉菜单选择目标账号
2. 点击"批量添加"按钮
3. 输入要添加的域名
4. 域名会添加到选择的 Account ID 下
```

### 示例3：统计所有账号的域名数量
```
1. 选择 Account ID: "所有账号"
2. 查看标题栏显示的总域名数
3. 逐个切换 Account ID 查看每个账号的域名数
```

## 更新日期
2025年11月15日
