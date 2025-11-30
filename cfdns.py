"""
Cloudflare DNS 域名管理工具 - 单文件版本
支持多账号管理
Author: Assistant
Date: 2025-11-10
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import requests
import json
import os

# ==================== 配置管理 ====================

CONFIG_FILE = "config.json"

class Config:
    def __init__(self):
        self.accounts = []  # 账号列表 [{"name": "账号名", "api_token": "token", "email": "email", "account_id": "id", "auth_type": "token"}]
        self.current_account_index = 0
        self.load_config()
    
    def load_config(self):
        """加载配置文件"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.accounts = data.get('accounts', [])
                    self.current_account_index = data.get('current_account_index', 0)
            except Exception as e:
                print(f"加载配置失败: {e}")
    
    def save_config(self):
        """保存配置文件"""
        try:
            data = {
                'accounts': self.accounts,
                'current_account_index': self.current_account_index
            }
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False
    
    def is_configured(self):
        """检查是否已配置"""
        return len(self.accounts) > 0
    
    def get_current_account(self):
        """获取当前账号"""
        if 0 <= self.current_account_index < len(self.accounts):
            return self.accounts[self.current_account_index]
        return None
    
    def add_account(self, name, api_token, account_id="", email="", auth_type="token"):
        """添加账号"""
        self.accounts.append({
            "name": name,
            "api_token": api_token,
            "account_id": account_id,
            "email": email,
            "auth_type": auth_type
        })
        return self.save_config()
    
    def update_account(self, index, name, api_token, account_id="", email="", auth_type="token"):
        """更新账号"""
        if 0 <= index < len(self.accounts):
            self.accounts[index] = {
                "name": name,
                "api_token": api_token,
                "account_id": account_id,
                "email": email,
                "auth_type": auth_type
            }
            return self.save_config()
        return False
    
    def delete_account(self, index):
        """删除账号"""
        if 0 <= index < len(self.accounts):
            self.accounts.pop(index)
            if self.current_account_index >= len(self.accounts):
                self.current_account_index = max(0, len(self.accounts) - 1)
            return self.save_config()
        return False
    
    def set_current_account(self, index):
        """设置当前账号"""
        if 0 <= index < len(self.accounts):
            self.current_account_index = index
            return self.save_config()
        return False

# 全局配置实例
config = Config()


# ==================== 工具函数 ====================

def center_window(window, parent=None):
    """将窗口居中显示"""
    window.update_idletasks()
    
    # 获取窗口尺寸
    window_width = window.winfo_width()
    window_height = window.winfo_height()
    
    if parent:
        # 相对于父窗口居中
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        
        x = parent_x + (parent_width - window_width) // 2
        y = parent_y + (parent_height - window_height) // 2
    else:
        # 相对于屏幕居中
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
    
    # 确保窗口不会超出屏幕
    x = max(0, x)
    y = max(0, y)
    
    window.geometry(f"+{x}+{y}")



# ==================== Cloudflare API ====================

class CloudflareAPI:
    def __init__(self, api_token, account_id="", email="", auth_type="token"):
        self.api_token = api_token
        self.account_id = account_id
        self.email = email
        self.auth_type = auth_type
        self.base_url = "https://api.cloudflare.com/client/v4"
        
        # 根据认证类型设置请求头
        if auth_type == "global_key":
            # Global API Key 认证方式
            self.headers = {
                "X-Auth-Email": email,
                "X-Auth-Key": api_token,
                "Content-Type": "application/json"
            }
        else:
            # API Token 认证方式（默认）
            self.headers = {
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/json"
            }
    
    def _request(self, method, endpoint, data=None, params=None):
        """统一请求方法"""
        url = f"{self.base_url}{endpoint}"
        try:
            if method == "GET":
                response = requests.get(url, headers=self.headers, params=params, timeout=30)
            elif method == "POST":
                response = requests.post(url, headers=self.headers, json=data, timeout=30)
            elif method == "PUT":
                response = requests.put(url, headers=self.headers, json=data, timeout=30)
            elif method == "PATCH":
                response = requests.patch(url, headers=self.headers, json=data, timeout=30)
            elif method == "DELETE":
                response = requests.delete(url, headers=self.headers, timeout=30)
            else:
                return None, "不支持的请求方法"
            
            # 检查HTTP状态码
            if response.status_code == 403:
                return None, "权限不足，请检查API Token权限"
            elif response.status_code == 401:
                return None, "认证失败，请检查API Token是否正确"
            elif response.status_code >= 500:
                return None, f"Cloudflare服务器错误 ({response.status_code})"
            
            result = response.json()
            if result.get('success'):
                return result.get('result'), None
            else:
                errors = result.get('errors', [])
                error_msg = errors[0].get('message', '未知错误') if errors else '请求失败'
                # 添加错误代码信息
                if errors and errors[0].get('code'):
                    error_msg += f" (代码: {errors[0].get('code')})"
                return None, error_msg
        except requests.exceptions.Timeout:
            return None, "请求超时，请检查网络连接"
        except requests.exceptions.ConnectionError:
            return None, "无法连接到Cloudflare，请检查网络"
        except Exception as e:
            return None, f"请求错误: {str(e)}"
    
    def verify_token(self):
        """验证 API Token 或 Global API Key"""
        # Global API Key 使用 /user 端点验证
        if self.auth_type == "global_key":
            result, error = self._request("GET", "/user")
        else:
            # API Token 使用 /user/tokens/verify 端点验证
            result, error = self._request("GET", "/user/tokens/verify")
        return error is None
    
    def get_accounts(self):
        """获取账号列表"""
        # 使用分页参数获取账号列表
        params = {
            "page": 1,
            "per_page": 50
        }
        return self._request("GET", "/accounts", params=params)
    
    def add_zone(self, domain, account_id=None):
        """添加域名到Cloudflare"""
        data = {
            "name": domain,
            "jump_start": True
        }
        # 如果指定了 account_id，则添加到指定账号
        if account_id:
            data["account"] = {"id": account_id}
        elif self.account_id:
            data["account"] = {"id": self.account_id}
        
        return self._request("POST", "/zones", data)
    
    def get_zones(self, account_id=None):
        """获取所有域名（支持分页）"""
        params = {
            "per_page": 50,  # 每页50条
            "page": 1
        }
        
        if account_id:
            params["account.id"] = account_id
        elif self.account_id:
            params["account.id"] = self.account_id
        
        all_zones = []
        
        while True:
            zones, error = self._request("GET", "/zones", params=params)
            
            if error:
                return None, error
            
            if not zones:
                break
            
            all_zones.extend(zones)
            
            # 检查是否还有更多页
            # 如果返回的记录数少于per_page，说明已经是最后一页
            if len(zones) < params["per_page"]:
                break
            
            params["page"] += 1
        
        return all_zones, None
    
    def get_zone_nameservers(self, zone_id):
        """获取域名的名称服务器"""
        result, error = self._request("GET", f"/zones/{zone_id}")
        if error:
            return None, error
        return result.get('name_servers', []), None
    
    def list_dns_records(self, zone_id):
        """列出DNS记录（支持分页）"""
        params = {
            "per_page": 100,  # 每页100条
            "page": 1
        }
        
        all_records = []
        
        while True:
            records, error = self._request("GET", f"/zones/{zone_id}/dns_records", params=params)
            
            if error:
                return None, error
            
            if not records:
                break
            
            all_records.extend(records)
            
            # 检查是否还有更多页
            if len(records) < params["per_page"]:
                break
            
            params["page"] += 1
        
        return all_records, None
    
    def add_dns_record(self, zone_id, record_type, name, content, proxied=False, ttl=1):
        """添加DNS记录"""
        data = {
            "type": record_type,
            "name": name,
            "content": content,
            "proxied": proxied,
            "ttl": ttl
        }
        return self._request("POST", f"/zones/{zone_id}/dns_records", data)
    
    def update_dns_record(self, zone_id, record_id, record_type, name, content, proxied=False, ttl=1):
        """更新DNS记录"""
        data = {
            "type": record_type,
            "name": name,
            "content": content,
            "proxied": proxied,
            "ttl": ttl
        }
        return self._request("PUT", f"/zones/{zone_id}/dns_records/{record_id}", data)
    
    def delete_dns_record(self, zone_id, record_id):
        """删除DNS记录"""
        return self._request("DELETE", f"/zones/{zone_id}/dns_records/{record_id}")
    
    def update_record_proxy_status(self, zone_id, record_id, proxied):
        """更新DNS记录的代理状态"""
        # 先获取当前记录信息
        result, error = self._request("GET", f"/zones/{zone_id}/dns_records/{record_id}")
        if error:
            return None, error
        
        record_type = result.get('type')
        
        # 只有A和AAAA记录支持代理
        if record_type not in ['A', 'AAAA']:
            return None, f"{record_type} 类型的记录不支持代理功能，只有 A 和 AAAA 记录可以使用代理"
        
        # 如果要开启代理，TTL必须设为1（自动）
        ttl = 1 if proxied else result.get('ttl', 1)
        
        data = {
            "type": record_type,
            "name": result.get('name'),
            "content": result.get('content'),
            "proxied": proxied,
            "ttl": ttl
        }
        
        # 如果有其他字段，也要包含
        if result.get('priority') is not None:
            data['priority'] = result.get('priority')
        
        return self._request("PATCH", f"/zones/{zone_id}/dns_records/{record_id}", data)
    
    def delete_zone(self, zone_id):
        """删除域名"""
        return self._request("DELETE", f"/zones/{zone_id}")


# ==================== 对话框界面 ====================

class AccountManageDialog:
    """账号管理对话框"""
    def __init__(self, parent):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("账号管理")
        self.dialog.geometry("700x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.setup_ui()
        self.refresh_accounts()
        
        # 居中显示
        center_window(self.dialog, parent)
    
    def setup_ui(self):
        """设置界面"""
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 顶部按钮
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(btn_frame, text="添加账号", command=self.add_account).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="编辑账号", command=self.edit_account).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="删除账号", command=self.delete_account).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="设为当前", command=self.set_current).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="验证Token", command=self.verify_token).pack(side=tk.LEFT, padx=2)
        
        # 账号列表
        columns = ("name", "account_id", "status")
        self.account_tree = ttk.Treeview(main_frame, columns=columns, show="headings", height=15)
        self.account_tree.heading("name", text="账号名称")
        self.account_tree.heading("account_id", text="Account ID")
        self.account_tree.heading("status", text="状态")
        
        self.account_tree.column("name", width=200)
        self.account_tree.column("account_id", width=300)
        self.account_tree.column("status", width=100)
        
        self.account_tree.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.account_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.account_tree.configure(yscrollcommand=scrollbar.set)
        
        # 底部关闭按钮
        ttk.Button(main_frame, text="关闭", command=self.dialog.destroy).pack(pady=(10, 0))
    
    def refresh_accounts(self):
        """刷新账号列表"""
        for item in self.account_tree.get_children():
            self.account_tree.delete(item)
        
        current_account = config.get_current_account()
        
        for i, account in enumerate(config.accounts):
            name = account.get('name', '未命名')
            account_id = account.get('account_id', '未设置')
            
            # 判断是否为当前账号
            status = "当前" if i == config.current_account_index else ""
            
            self.account_tree.insert("", tk.END, iid=str(i), values=(name, account_id, status))
    
    def add_account(self):
        """添加账号"""
        dialog = AccountEditDialog(self.dialog, "添加账号")
        self.dialog.wait_window(dialog.dialog)
        
        if dialog.result:
            config.add_account(
                dialog.result['name'], 
                dialog.result['api_token'], 
                dialog.result['account_id'],
                dialog.result.get('email', ''),
                dialog.result.get('auth_type', 'token')
            )
            self.refresh_accounts()
            messagebox.showinfo("成功", "账号添加成功")
    
    def edit_account(self):
        """编辑账号"""
        selection = self.account_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择账号")
            return
        
        index = int(selection[0])
        account = config.accounts[index]
        
        dialog = AccountEditDialog(self.dialog, "编辑账号", account)
        self.dialog.wait_window(dialog.dialog)
        
        if dialog.result:
            config.update_account(
                index, 
                dialog.result['name'], 
                dialog.result['api_token'], 
                dialog.result['account_id'],
                dialog.result.get('email', ''),
                dialog.result.get('auth_type', 'token')
            )
            self.refresh_accounts()
            messagebox.showinfo("成功", "账号更新成功")
    
    def delete_account(self):
        """删除账号"""
        selection = self.account_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择账号")
            return
        
        index = int(selection[0])
        account = config.accounts[index]
        
        if messagebox.askyesno("确认", f"确定要删除账号 {account['name']} 吗？"):
            config.delete_account(index)
            self.refresh_accounts()
            messagebox.showinfo("成功", "账号删除成功")
    
    def set_current(self):
        """设置当前账号"""
        selection = self.account_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择账号")
            return
        
        index = int(selection[0])
        config.set_current_account(index)
        self.refresh_accounts()
        messagebox.showinfo("成功", "已切换当前账号")
    
    def verify_token(self):
        """验证Token"""
        selection = self.account_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择账号")
            return
        
        index = int(selection[0])
        account = config.accounts[index]
        
        api = CloudflareAPI(
            account['api_token'], 
            account.get('account_id', ''),
            account.get('email', ''),
            account.get('auth_type', 'token')
        )
        if api.verify_token():
            auth_type_name = "Global API Key" if account.get('auth_type') == 'global_key' else "API Token"
            messagebox.showinfo("成功", f"账号 {account['name']} 的 {auth_type_name} 验证成功")
        else:
            messagebox.showerror("错误", f"账号 {account['name']} 的认证验证失败")


class AccountEditDialog:
    """账号编辑对话框"""
    def __init__(self, parent, title, account=None):
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("500x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.setup_ui(account)
        
        # 居中显示
        center_window(self.dialog, parent)
    
    def setup_ui(self, account):
        """设置界面"""
        frame = ttk.Frame(self.dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # 账号名称
        ttk.Label(frame, text="账号名称:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.name_entry = ttk.Entry(frame, width=50)
        self.name_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        if account:
            self.name_entry.insert(0, account.get('name', ''))
        
        # 认证类型
        ttk.Label(frame, text="认证类型:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.auth_type_var = tk.StringVar(value=account.get('auth_type', 'token') if account else 'token')
        
        auth_frame = ttk.Frame(frame)
        auth_frame.grid(row=1, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        
        ttk.Radiobutton(auth_frame, text="API Token", variable=self.auth_type_var, 
                       value="token", command=self.on_auth_type_change).pack(side=tk.LEFT, padx=(0, 15))
        ttk.Radiobutton(auth_frame, text="Global API Key", variable=self.auth_type_var, 
                       value="global_key", command=self.on_auth_type_change).pack(side=tk.LEFT)
        
        # Email（Global API Key 需要）
        ttk.Label(frame, text="Email:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.email_entry = ttk.Entry(frame, width=50)
        self.email_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        if account:
            self.email_entry.insert(0, account.get('email', ''))
        
        self.email_label = ttk.Label(frame, text="(Global API Key 需要)", foreground="gray")
        self.email_label.grid(row=3, column=1, sticky=tk.W)
        
        # API Token / Global API Key
        self.token_label = ttk.Label(frame, text="API Token:")
        self.token_label.grid(row=4, column=0, sticky=tk.W, pady=5)
        self.token_entry = ttk.Entry(frame, width=50, show="*")
        self.token_entry.grid(row=4, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        if account:
            self.token_entry.insert(0, account.get('api_token', ''))
        
        # Account ID
        ttk.Label(frame, text="Account ID:").grid(row=5, column=0, sticky=tk.W, pady=5)
        
        account_frame = ttk.Frame(frame)
        account_frame.grid(row=5, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        self.account_id_entry = ttk.Entry(account_frame, width=40)
        self.account_id_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        if account:
            self.account_id_entry.insert(0, account.get('account_id', ''))
        
        ttk.Button(account_frame, text="获取", command=self.fetch_accounts).pack(side=tk.LEFT, padx=(5, 0))
        
        ttk.Label(frame, text="(可选，留空则显示所有账号下的域名)", foreground="gray").grid(row=6, column=1, sticky=tk.W)
        
        # 说明
        info_frame = ttk.LabelFrame(frame, text="说明", padding="10")
        info_frame.grid(row=7, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        info_text = "认证方式:\n"
        info_text += "• API Token: 推荐，需要在控制台创建（权限可控）\n"
        info_text += "• Global API Key: 完整权限，需要配合 Email 使用\n\n"
        info_text += "Token 权限（仅 API Token）:\n"
        info_text += "  必需: Zone - Zone - Read, Zone - DNS - Edit\n"
        info_text += "  可选: Account - Account - Read (自动获取Account ID)\n\n"
        info_text += "Account ID: 可选，指定后只显示该账号下的域名"
        
        ttk.Label(info_frame, text=info_text, justify=tk.LEFT).pack()
        
        # 按钮
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=8, column=0, columnspan=2, pady=20)
        
        ttk.Button(btn_frame, text="保存", command=self.save).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        frame.columnconfigure(1, weight=1)
        
        # 初始化界面状态
        self.on_auth_type_change()
    
    def on_auth_type_change(self):
        """认证类型改变时的处理"""
        auth_type = self.auth_type_var.get()
        
        if auth_type == "global_key":
            self.token_label.config(text="Global API Key:")
            self.email_entry.config(state="normal")
            self.email_label.config(text="(必需：Cloudflare 账号邮箱)", foreground="red")
        else:
            self.token_label.config(text="API Token:")
            self.email_entry.config(state="normal")
            self.email_label.config(text="(Global API Key 需要)", foreground="gray")
    
    def fetch_accounts(self):
        """获取账号列表"""
        token = self.token_entry.get().strip()
        email = self.email_entry.get().strip()
        auth_type = self.auth_type_var.get()
        
        if not token:
            messagebox.showwarning("警告", "请先输入 API Token 或 Global API Key")
            return
        
        if auth_type == "global_key" and not email:
            messagebox.showwarning("警告", "使用 Global API Key 需要输入邮箱")
            return
        
        # 显示获取中提示
        try:
            self.dialog.config(cursor="wait")
            self.dialog.update()
        except:
            pass
        
        success = False
        try:
            api = CloudflareAPI(token, email=email, auth_type=auth_type)
            
            # 先验证Token
            if not api.verify_token():
                messagebox.showerror("错误", "认证失败，请检查配置是否正确")
                return
            
            # 获取账号列表
            accounts, error = api.get_accounts()
            
            if error:
                if auth_type == "global_key":
                    error_detail = f"获取账号列表失败: {error}\n\n"
                    error_detail += "请确认:\n"
                    error_detail += "1. Global API Key 正确\n"
                    error_detail += "2. Email 地址正确\n"
                    error_detail += "3. 账号状态正常"
                else:
                    error_detail = f"获取账号列表失败: {error}\n\n"
                    error_detail += "可能的原因:\n"
                    error_detail += "1. Token 权限不足（需要 Account:Read 权限）\n"
                    error_detail += "2. Token 未授权访问账号信息\n"
                    error_detail += "3. 网络连接问题\n\n"
                    error_detail += "建议:\n"
                    error_detail += "• 重新创建 Token 时勾选 Account - Account - Read 权限\n"
                    error_detail += "• 或直接在 Cloudflare 控制台复制 Account ID"
                messagebox.showerror("错误", error_detail)
                return
            
            if not accounts:
                messagebox.showinfo("提示", "未找到账号信息\n\n可能是认证配置没有账号访问权限。\n你可以直接在 Cloudflare 控制台复制 Account ID。")
                return
            
            success = True
            # 显示账号选择对话框
            AccountSelectDialog(self.dialog, accounts, self.account_id_entry)
            
        except Exception as e:
            messagebox.showerror("错误", f"发生错误: {str(e)}")
        finally:
            # 恢复光标（无论成功与否）
            try:
                self.dialog.config(cursor="")
                if not success:
                    self.dialog.update()
            except:
                # 如果对话框已关闭，忽略错误
                pass
    
    def save(self):
        """保存"""
        name = self.name_entry.get().strip()
        token = self.token_entry.get().strip()
        account_id = self.account_id_entry.get().strip()
        email = self.email_entry.get().strip()
        auth_type = self.auth_type_var.get()
        
        if not name:
            messagebox.showwarning("警告", "请输入账号名称")
            return
        
        if not token:
            messagebox.showwarning("警告", "请输入 API Token 或 Global API Key")
            return
        
        if auth_type == "global_key" and not email:
            messagebox.showwarning("警告", "使用 Global API Key 需要输入邮箱")
            return
        
        self.result = {
            "name": name,
            "api_token": token,
            "account_id": account_id,
            "email": email,
            "auth_type": auth_type
        }
        self.dialog.destroy()


class AccountSelectDialog:
    """账号选择对话框"""
    def __init__(self, parent, accounts, target_entry):
        self.accounts = accounts
        self.target_entry = target_entry
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("选择 Account ID")
        self.dialog.geometry("600x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.setup_ui()
        
        # 居中显示
        center_window(self.dialog, parent)
    
    def setup_ui(self):
        """设置界面"""
        frame = ttk.Frame(self.dialog, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="选择一个账号：").pack(anchor=tk.W, pady=(0, 5))
        
        # 账号列表
        columns = ("name", "id")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings", height=15)
        self.tree.heading("name", text="账号名称")
        self.tree.heading("id", text="Account ID")
        
        self.tree.column("name", width=200)
        self.tree.column("id", width=350)
        
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        for account in self.accounts:
            account_id = account.get('id', '')
            account_name = account.get('name', '未命名')
            self.tree.insert("", tk.END, values=(account_name, account_id))
        
        self.tree.bind("<Double-1>", lambda e: self.select_account())
        
        # 按钮
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=(10, 0))
        
        ttk.Button(btn_frame, text="选择", command=self.select_account).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def select_account(self):
        """选择账号"""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = self.tree.item(selection[0])
        account_id = item['values'][1]
        
        self.target_entry.delete(0, tk.END)
        self.target_entry.insert(0, account_id)
        
        self.dialog.destroy()


class AddDomainDialog:
    """添加域名对话框"""
    def __init__(self, parent, api):
        self.api = api
        self.success = False
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("添加域名")
        self.dialog.geometry("500x250")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.setup_ui()
        
        # 居中显示
        center_window(self.dialog, parent)
    
    def setup_ui(self):
        """设置界面"""
        frame = ttk.Frame(self.dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # 域名
        ttk.Label(frame, text="域名:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.domain_entry = ttk.Entry(frame, width=40)
        self.domain_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        self.domain_entry.focus()
        
        ttk.Label(frame, text="示例: example.com", foreground="gray").grid(row=1, column=1, sticky=tk.W)
        
        # Account ID
        ttk.Label(frame, text="Account ID:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.account_id_entry = ttk.Entry(frame, width=40)
        self.account_id_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        # 默认填充当前账号的 Account ID
        current_account = config.get_current_account()
        if current_account and current_account.get('account_id'):
            self.account_id_entry.insert(0, current_account['account_id'])
        
        ttk.Label(frame, text="(可选，留空则添加到默认账号)", foreground="gray").grid(row=3, column=1, sticky=tk.W)
        
        # 按钮
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=20)
        
        ttk.Button(btn_frame, text="添加", command=self.add_domain).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        frame.columnconfigure(1, weight=1)
        
        self.domain_entry.bind("<Return>", lambda e: self.add_domain())
    
    def add_domain(self):
        """添加域名"""
        domain = self.domain_entry.get().strip()
        account_id = self.account_id_entry.get().strip()
        
        if not domain:
            messagebox.showwarning("警告", "请输入域名")
            return
        
        result, error = self.api.add_zone(domain, account_id if account_id else None)
        
        if error:
            messagebox.showerror("错误", f"添加域名失败: {error}")
        else:
            self.success = True
            name_servers = result.get('name_servers', [])
            
            msg = f"域名 {domain} 添加成功!\n\n"
            if name_servers:
                msg += "请将域名的DNS服务器更改为:\n\n"
                for ns in name_servers:
                    msg += f"  • {ns}\n"
            
            messagebox.showinfo("成功", msg)
            self.dialog.destroy()


class BatchAddDialog:
    """批量添加域名对话框"""
    def __init__(self, parent, api):
        self.api = api
        self.success = False
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("批量添加域名")
        self.dialog.geometry("700x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.setup_ui()
        
        # 居中显示
        center_window(self.dialog, parent)
    
    def setup_ui(self):
        """设置界面"""
        frame = ttk.Frame(self.dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Account ID
        account_frame = ttk.Frame(frame)
        account_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(account_frame, text="Account ID:").pack(side=tk.LEFT)
        self.account_id_entry = ttk.Entry(account_frame, width=40)
        self.account_id_entry.pack(side=tk.LEFT, padx=(10, 0), fill=tk.X, expand=True)
        
        # 默认填充当前账号的 Account ID
        current_account = config.get_current_account()
        if current_account and current_account.get('account_id'):
            self.account_id_entry.insert(0, current_account['account_id'])
        
        ttk.Label(frame, text="域名列表 (每行一个):").pack(anchor=tk.W, pady=(0, 5))
        
        self.domain_text = scrolledtext.ScrolledText(frame, width=70, height=15)
        self.domain_text.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="示例:\nexample.com\ntest.com\nmysite.org", 
                 foreground="gray", justify=tk.LEFT).pack(anchor=tk.W, pady=(5, 0))
        
        # 按钮
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="开始添加", command=self.batch_add).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        # 进度
        self.progress_label = ttk.Label(frame, text="")
        self.progress_label.pack()
    
    def batch_add(self):
        """批量添加域名"""
        content = self.domain_text.get(1.0, tk.END).strip()
        account_id = self.account_id_entry.get().strip()
        
        if not content:
            messagebox.showwarning("警告", "请输入域名")
            return
        
        domains = [line.strip() for line in content.split('\n') if line.strip()]
        
        if not domains:
            messagebox.showwarning("警告", "没有有效的域名")
            return
        
        if not messagebox.askyesno("确认", f"确定要添加 {len(domains)} 个域名吗?"):
            return
        
        success_count = 0
        fail_count = 0
        results = []
        
        for i, domain in enumerate(domains, 1):
            self.progress_label.config(text=f"正在添加 {i}/{len(domains)}: {domain}")
            self.dialog.update()
            
            result, error = self.api.add_zone(domain, account_id if account_id else None)
            
            if error:
                fail_count += 1
                results.append(f"❌ {domain}: {error}")
            else:
                success_count += 1
                name_servers = result.get('name_servers', [])
                ns_info = ', '.join(name_servers) if name_servers else '无'
                results.append(f"✓ {domain}: {ns_info}")
        
        self.success = success_count > 0
        
        # 显示结果
        result_dialog = tk.Toplevel(self.dialog)
        result_dialog.title("批量添加结果")
        result_dialog.geometry("800x500")
        result_dialog.transient(self.dialog)
        
        result_frame = ttk.Frame(result_dialog, padding="20")
        result_frame.pack(fill=tk.BOTH, expand=True)
        
        summary = f"成功: {success_count}, 失败: {fail_count}\n\n"
        ttk.Label(result_frame, text=summary, font=('TkDefaultFont', 10, 'bold')).pack(anchor=tk.W)
        
        result_text = scrolledtext.ScrolledText(result_frame, width=90, height=20)
        result_text.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        for line in results:
            result_text.insert(tk.END, line + '\n')
        
        result_text.config(state=tk.DISABLED)
        
        ttk.Button(result_frame, text="关闭", 
                  command=lambda: [result_dialog.destroy(), self.dialog.destroy()]).pack(pady=(10, 0))


class AddRecordDialog:
    """添加DNS记录对话框"""
    def __init__(self, parent, api, zone_id):
        self.api = api
        self.zone_id = zone_id
        self.success = False
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("添加DNS记录")
        self.dialog.geometry("500x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.setup_ui()
        
        # 居中显示
        center_window(self.dialog, parent)
    
    def setup_ui(self):
        """设置界面"""
        frame = ttk.Frame(self.dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # 类型
        ttk.Label(frame, text="类型:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.type_combo = ttk.Combobox(frame, width=15, state="readonly")
        self.type_combo['values'] = ('A', 'AAAA', 'CNAME', 'MX', 'TXT', 'NS', 'SRV')
        self.type_combo.current(0)
        self.type_combo.grid(row=0, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        
        # 名称
        ttk.Label(frame, text="名称:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.name_entry = ttk.Entry(frame, width=40)
        self.name_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        # 内容
        ttk.Label(frame, text="内容:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.content_entry = ttk.Entry(frame, width=40)
        self.content_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        # 代理
        self.proxy_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(frame, text="启用代理 (仅支持A、AAAA、CNAME记录)", 
                       variable=self.proxy_var).grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # TTL
        ttk.Label(frame, text="TTL:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.ttl_combo = ttk.Combobox(frame, width=15, state="readonly")
        self.ttl_combo['values'] = ('Auto', '120', '300', '600', '1800', '3600', '7200', '18000', '43200', '86400')
        self.ttl_combo.current(0)
        self.ttl_combo.grid(row=4, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        
        # 按钮
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=20)
        
        ttk.Button(btn_frame, text="添加", command=self.add_record).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        frame.columnconfigure(1, weight=1)
    
    def add_record(self):
        """添加DNS记录"""
        record_type = self.type_combo.get()
        name = self.name_entry.get().strip()
        content = self.content_entry.get().strip()
        proxied = self.proxy_var.get()
        ttl_str = self.ttl_combo.get()
        ttl = 1 if ttl_str == 'Auto' else int(ttl_str)
        
        if not name or not content:
            messagebox.showwarning("警告", "请填写所有必填字段")
            return
        
        result, error = self.api.add_dns_record(self.zone_id, record_type, name, content, proxied, ttl)
        
        if error:
            messagebox.showerror("错误", f"添加DNS记录失败: {error}")
        else:
            self.success = True
            messagebox.showinfo("成功", "DNS记录添加成功")
            self.dialog.destroy()


class EditRecordDialog:
    """修改DNS记录对话框"""
    def __init__(self, parent, api, zone_id, record_id):
        self.api = api
        self.zone_id = zone_id
        self.record_id = record_id
        self.success = False
        self.record_data = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("修改DNS记录")
        self.dialog.geometry("500x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 先获取记录数据
        self.load_record_data()
        
        if self.record_data:
            self.setup_ui()
            
            # 居中显示
            center_window(self.dialog, parent)
    
    def load_record_data(self):
        """加载记录数据"""
        result, error = self.api._request("GET", f"/zones/{self.zone_id}/dns_records/{self.record_id}")
        if error:
            messagebox.showerror("错误", f"获取记录信息失败: {error}")
            self.dialog.destroy()
        else:
            self.record_data = result
    
    def setup_ui(self):
        """设置界面"""
        frame = ttk.Frame(self.dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # 类型（只读，显示为标签）
        ttk.Label(frame, text="类型:").grid(row=0, column=0, sticky=tk.W, pady=5)
        record_type = self.record_data.get('type', '')
        type_label = ttk.Label(frame, text=record_type, 
                              foreground="blue", font=('TkDefaultFont', 10, 'bold'))
        type_label.grid(row=0, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        
        # 名称
        ttk.Label(frame, text="名称:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.name_entry = ttk.Entry(frame, width=40)
        self.name_entry.insert(0, self.record_data.get('name', ''))
        self.name_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        # 内容
        ttk.Label(frame, text="内容:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.content_entry = ttk.Entry(frame, width=40)
        self.content_entry.insert(0, self.record_data.get('content', ''))
        self.content_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        current_row = 3
        
        # MX记录的优先级
        if record_type == 'MX':
            ttk.Label(frame, text="优先级:").grid(row=current_row, column=0, sticky=tk.W, pady=5)
            self.priority_entry = ttk.Entry(frame, width=15)
            priority = self.record_data.get('priority', 10)
            self.priority_entry.insert(0, str(priority))
            self.priority_entry.grid(row=current_row, column=1, sticky=tk.W, pady=5, padx=(10, 0))
            current_row += 1
        else:
            self.priority_entry = None
        
        # SRV记录的额外字段
        if record_type == 'SRV':
            # 优先级
            ttk.Label(frame, text="优先级:").grid(row=current_row, column=0, sticky=tk.W, pady=5)
            self.priority_entry = ttk.Entry(frame, width=15)
            self.priority_entry.insert(0, str(self.record_data.get('priority', 0)))
            self.priority_entry.grid(row=current_row, column=1, sticky=tk.W, pady=5, padx=(10, 0))
            current_row += 1
            
            # 权重
            ttk.Label(frame, text="权重:").grid(row=current_row, column=0, sticky=tk.W, pady=5)
            self.weight_entry = ttk.Entry(frame, width=15)
            srv_data = self.record_data.get('data', {})
            self.weight_entry.insert(0, str(srv_data.get('weight', 0)))
            self.weight_entry.grid(row=current_row, column=1, sticky=tk.W, pady=5, padx=(10, 0))
            current_row += 1
            
            # 端口
            ttk.Label(frame, text="端口:").grid(row=current_row, column=0, sticky=tk.W, pady=5)
            self.port_entry = ttk.Entry(frame, width=15)
            self.port_entry.insert(0, str(srv_data.get('port', 0)))
            self.port_entry.grid(row=current_row, column=1, sticky=tk.W, pady=5, padx=(10, 0))
            current_row += 1
        else:
            self.weight_entry = None
            self.port_entry = None
        
        # 代理选项（只对A、AAAA和CNAME记录显示）
        if record_type in ['A', 'AAAA', 'CNAME']:
            self.proxy_var = tk.BooleanVar(value=self.record_data.get('proxied', False))
            proxy_text = "启用代理" if record_type in ['A', 'AAAA'] else "启用代理 (CNAME记录)"
            ttk.Checkbutton(frame, text=proxy_text, 
                           variable=self.proxy_var).grid(row=current_row, column=0, columnspan=2, sticky=tk.W, pady=5)
        else:
            self.proxy_var = None
            ttk.Label(frame, text=f"({record_type} 记录不支持代理)", 
                     foreground="gray").grid(row=current_row, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        current_row += 1
        
        # TTL
        ttl_label = "TTL:" if record_type != 'A' and record_type != 'AAAA' else "TTL (代理开启时自动为Auto):"
        ttk.Label(frame, text=ttl_label).grid(row=current_row, column=0, sticky=tk.W, pady=5)
        self.ttl_combo = ttk.Combobox(frame, width=15, state="readonly")
        self.ttl_combo['values'] = ('Auto', '120', '300', '600', '1800', '3600', '7200', '18000', '43200', '86400')
        
        current_ttl = self.record_data.get('ttl', 1)
        if current_ttl == 1:
            self.ttl_combo.current(0)  # Auto
        elif str(current_ttl) in self.ttl_combo['values']:
            self.ttl_combo.set(str(current_ttl))
        else:
            self.ttl_combo.current(0)
        
        self.ttl_combo.grid(row=current_row, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        current_row += 1
        
        # 按钮
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=current_row, column=0, columnspan=2, pady=20)
        
        ttk.Button(btn_frame, text="保存", command=self.save_record).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        frame.columnconfigure(1, weight=1)
    
    def save_record(self):
        """保存修改"""
        name = self.name_entry.get().strip()
        content = self.content_entry.get().strip()
        ttl_str = self.ttl_combo.get()
        ttl = 1 if ttl_str == 'Auto' else int(ttl_str)
        record_type = self.record_data.get('type')
        
        if not name or not content:
            messagebox.showwarning("警告", "名称和内容不能为空")
            return
        
        # 构建更新数据
        data = {
            "type": record_type,
            "name": name,
            "content": content,
            "ttl": ttl
        }
        
        # 如果支持代理，添加代理状态
        if self.proxy_var:
            data["proxied"] = self.proxy_var.get()
            # 如果开启代理，TTL必须为1
            if data["proxied"]:
                data["ttl"] = 1
        else:
            data["proxied"] = self.record_data.get('proxied', False)
        
        # MX记录的优先级
        if record_type == 'MX' and self.priority_entry:
            try:
                priority = int(self.priority_entry.get().strip())
                data['priority'] = priority
            except ValueError:
                messagebox.showwarning("警告", "优先级必须是数字")
                return
        
        # SRV记录的额外字段
        if record_type == 'SRV':
            try:
                if self.priority_entry:
                    data['priority'] = int(self.priority_entry.get().strip())
                
                srv_data = {}
                if self.weight_entry:
                    srv_data['weight'] = int(self.weight_entry.get().strip())
                if self.port_entry:
                    srv_data['port'] = int(self.port_entry.get().strip())
                
                # SRV记录还需要service、proto和target
                if self.record_data.get('data'):
                    old_data = self.record_data.get('data', {})
                    srv_data['service'] = old_data.get('service', '_service')
                    srv_data['proto'] = old_data.get('proto', '_tcp')
                    srv_data['name'] = name
                    srv_data['target'] = content
                
                data['data'] = srv_data
            except ValueError:
                messagebox.showwarning("警告", "优先级、权重和端口必须是数字")
                return
        
        # 发送更新请求
        result, error = self.api._request("PATCH", f"/zones/{self.zone_id}/dns_records/{self.record_id}", data)
        
        if error:
            messagebox.showerror("错误", f"更新DNS记录失败: {error}")
        else:
            self.success = True
            messagebox.showinfo("成功", "DNS记录更新成功")
            self.dialog.destroy()


class BatchAddRecordsDialog:
    """批量添加DNS记录对话框"""
    def __init__(self, parent, api, zone_id):
        self.api = api
        self.zone_id = zone_id
        self.success = False
        self.record_rows = []  # 存储所有记录行
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("批量添加DNS记录")
        self.dialog.geometry("1000x700")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.setup_ui()
        
        # 居中显示
        center_window(self.dialog, parent)
    
    def setup_ui(self):
        """设置界面"""
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 顶部说明
        instruction = ttk.Label(main_frame, 
                               text="批量添加DNS记录 - 使用表格方式输入多条记录",
                               font=('TkDefaultFont', 10, 'bold'),
                               foreground="blue")
        instruction.pack(anchor=tk.W, pady=(0, 10))
        
        # 按钮栏
        btn_top_frame = ttk.Frame(main_frame)
        btn_top_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(btn_top_frame, text="➕ 添加一行", command=self.add_row).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_top_frame, text="➕ 添加5行", command=lambda: self.add_multiple_rows(5)).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_top_frame, text="🗑️ 删除选中行", command=self.delete_selected_rows).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_top_frame, text="🧹 清空所有", command=self.clear_all_rows).pack(side=tk.LEFT, padx=2)
        
        # 创建滚动区域
        scroll_frame = ttk.Frame(main_frame)
        scroll_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建Canvas和Scrollbar
        canvas = tk.Canvas(scroll_frame, height=500)
        scrollbar_y = ttk.Scrollbar(scroll_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollbar_x = ttk.Scrollbar(scroll_frame, orient=tk.HORIZONTAL, command=canvas.xview)
        
        self.records_frame = ttk.Frame(canvas)
        
        # 配置Canvas
        canvas.create_window((0, 0), window=self.records_frame, anchor=tk.NW)
        canvas.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        # 布局
        canvas.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))
        scrollbar_y.grid(row=0, column=1, sticky=(tk.N, tk.S))
        scrollbar_x.grid(row=1, column=0, sticky=(tk.E, tk.W))
        
        scroll_frame.grid_rowconfigure(0, weight=1)
        scroll_frame.grid_columnconfigure(0, weight=1)
        
        self.canvas = canvas
        
        # 表头
        self.create_header()
        
        # 添加初始行
        self.add_multiple_rows(5)
        
        # 更新滚动区域
        self.records_frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))
        
        # 底部按钮
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(bottom_frame, text="✅ 开始添加", 
                  command=self.batch_add, 
                  style='Accent.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_frame, text="❌ 取消", 
                  command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def create_header(self):
        """创建表头"""
        header_frame = ttk.Frame(self.records_frame, relief=tk.RAISED, borderwidth=1)
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=2, pady=2)
        
        headers = [
            ("☑", 3),      # 选择框
            ("类型", 10),
            ("名称", 20),
            ("内容", 30),
            ("代理", 8),
            ("TTL", 10),
            ("优先级", 8)
        ]
        
        for col, (text, width) in enumerate(headers):
            label = ttk.Label(header_frame, text=text, font=('TkDefaultFont', 9, 'bold'), width=width)
            label.grid(row=0, column=col, padx=2, pady=5, sticky=tk.W)
    
    def add_row(self):
        """添加一行输入"""
        row_num = len(self.record_rows) + 1  # +1 因为第0行是表头
        
        row_frame = ttk.Frame(self.records_frame)
        row_frame.grid(row=row_num, column=0, sticky=(tk.W, tk.E), padx=2, pady=1)
        
        # 选择框
        selected_var = tk.BooleanVar(value=False)
        cb = ttk.Checkbutton(row_frame, variable=selected_var, width=3)
        cb.grid(row=0, column=0, padx=2)
        
        # 类型下拉框
        type_combo = ttk.Combobox(row_frame, width=8, state="readonly")
        type_combo['values'] = ('A', 'AAAA', 'CNAME', 'MX', 'TXT', 'NS', 'SRV', 'CAA')
        type_combo.current(0)
        type_combo.grid(row=0, column=1, padx=2)
        
        # 名称输入框
        name_entry = ttk.Entry(row_frame, width=18)
        name_entry.insert(0, "@")
        name_entry.grid(row=0, column=2, padx=2)
        
        # 内容输入框
        content_entry = ttk.Entry(row_frame, width=28)
        content_entry.grid(row=0, column=3, padx=2)
        
        # 代理下拉框
        proxy_combo = ttk.Combobox(row_frame, width=6, state="readonly")
        proxy_combo['values'] = ('关闭', '开启')
        proxy_combo.current(0)
        proxy_combo.grid(row=0, column=4, padx=2)
        
        # TTL下拉框
        ttl_combo = ttk.Combobox(row_frame, width=8, state="readonly")
        ttl_combo['values'] = ('Auto', '120', '300', '600', '1800', '3600', '7200', '18000', '43200', '86400')
        ttl_combo.current(0)
        ttl_combo.grid(row=0, column=5, padx=2)
        
        # 优先级输入框（仅MX和SRV需要）
        priority_entry = ttk.Entry(row_frame, width=6)
        priority_entry.grid(row=0, column=6, padx=2)
        
        # 保存行数据
        row_data = {
            'frame': row_frame,
            'selected': selected_var,
            'type': type_combo,
            'name': name_entry,
            'content': content_entry,
            'proxy': proxy_combo,
            'ttl': ttl_combo,
            'priority': priority_entry
        }
        
        self.record_rows.append(row_data)
        
        # 更新Canvas滚动区域
        self.records_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def add_multiple_rows(self, count):
        """添加多行"""
        for _ in range(count):
            self.add_row()
    
    def delete_selected_rows(self):
        """删除选中的行"""
        # 从后向前删除，避免索引问题
        for i in range(len(self.record_rows) - 1, -1, -1):
            if self.record_rows[i]['selected'].get():
                self.record_rows[i]['frame'].destroy()
                self.record_rows.pop(i)
        
        # 重新编号
        for i, row_data in enumerate(self.record_rows):
            row_data['frame'].grid(row=i + 1, column=0, sticky=(tk.W, tk.E), padx=2, pady=1)
        
        # 更新Canvas滚动区域
        self.records_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def clear_all_rows(self):
        """清空所有行"""
        if not messagebox.askyesno("确认", "确定要清空所有记录吗？"):
            return
        
        for row_data in self.record_rows:
            row_data['frame'].destroy()
        
        self.record_rows.clear()
        
        # 更新Canvas滚动区域
        self.records_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def batch_add(self):
        """批量添加DNS记录"""
        # 收集所有非空行
        records_to_add = []
        
        for i, row_data in enumerate(self.record_rows):
            record_type = row_data['type'].get()
            name = row_data['name'].get().strip()
            content = row_data['content'].get().strip()
            
            # 跳过空行
            if not name and not content:
                continue
            
            # 验证必填字段
            if not name or not content:
                messagebox.showwarning("警告", f"第 {i+1} 行：名称和内容不能为空！")
                return
            
            # 获取代理状态
            proxy_text = row_data['proxy'].get()
            proxied = (proxy_text == '开启')
            
            # 获取TTL
            ttl_text = row_data['ttl'].get()
            if ttl_text.lower() in ['auto', 'automatic']:
                ttl = 1
            else:
                try:
                    ttl = int(ttl_text)
                except ValueError:
                    ttl = 1
            
            # 获取优先级
            priority_text = row_data['priority'].get().strip()
            priority = None
            if priority_text and record_type in ['MX', 'SRV', 'URI']:
                try:
                    priority = int(priority_text)
                except ValueError:
                    pass
            
            records_to_add.append((i + 1, record_type, name, content, proxied, ttl, priority))
        
        if not records_to_add:
            messagebox.showwarning("警告", "请至少输入一条DNS记录！")
            return
        
        # 确认
        if not messagebox.askyesno("确认", f"确定要添加 {len(records_to_add)} 条DNS记录吗？"):
            return
        
        success_count = 0
        fail_count = 0
        results = []
        
        for row_num, record_type, name, content, proxied, ttl, priority in records_to_add:
            try:
                # 添加记录
                if record_type == 'MX' and priority is not None:
                    # MX记录需要特殊处理
                    data = {
                        "type": record_type,
                        "name": name,
                        "content": content,
                        "proxied": proxied,
                        "ttl": ttl,
                        "priority": priority
                    }
                    result, error = self.api._request("POST", f"/zones/{self.zone_id}/dns_records", data)
                else:
                    result, error = self.api.add_dns_record(
                        self.zone_id, 
                        record_type, 
                        name, 
                        content, 
                        proxied, 
                        ttl
                    )
                
                if error:
                    results.append(f"[失败] 第{row_num}行 ({record_type} {name}): {error}")
                    fail_count += 1
                else:
                    results.append(f"[成功] 第{row_num}行 ({record_type} {name}): 添加成功")
                    success_count += 1
                    
            except Exception as e:
                results.append(f"[错误] 第{row_num}行：{str(e)}")
                fail_count += 1
        
        # 显示结果
        self.show_results(success_count, fail_count, results)
        
        if success_count > 0:
            self.success = True
    
    def show_results(self, success_count, fail_count, results):
        """显示批量操作结果"""
        result_dialog = tk.Toplevel(self.dialog)
        result_dialog.title("批量添加结果")
        result_dialog.geometry("900x500")
        result_dialog.transient(self.dialog)
        
        result_frame = ttk.Frame(result_dialog, padding="20")
        result_frame.pack(fill=tk.BOTH, expand=True)
        
        summary = f"成功: {success_count}, 失败: {fail_count}\n\n"
        ttk.Label(result_frame, text=summary, font=('TkDefaultFont', 10, 'bold')).pack(anchor=tk.W)
        
        result_text = scrolledtext.ScrolledText(result_frame, width=100, height=20)
        result_text.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        for line in results:
            result_text.insert(tk.END, line + '\n')
        
        result_text.config(state=tk.DISABLED)
        
        ttk.Button(result_frame, text="关闭", 
                  command=lambda: [result_dialog.destroy(), self.dialog.destroy()]).pack(pady=(10, 0))


class BatchEditRecordsDialog:
    """批量修改DNS记录对话框"""
    def __init__(self, parent, api, zone_id, selected_records):
        self.api = api
        self.zone_id = zone_id
        self.selected_records = selected_records  # [(record_id, record_data), ...]
        self.success = False
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"批量修改DNS记录 (已选择 {len(selected_records)} 条)")
        self.dialog.geometry("700x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.setup_ui()
        
        # 居中显示
        center_window(self.dialog, parent)
    
    def setup_ui(self):
        """设置界面"""
        frame = ttk.Frame(self.dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # 说明
        ttk.Label(frame, text="批量修改选中的DNS记录", 
                 font=('TkDefaultFont', 10, 'bold')).pack(anchor=tk.W, pady=(0, 10))
        
        # 显示选中的记录
        list_frame = ttk.LabelFrame(frame, text="选中的记录", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        list_text = scrolledtext.ScrolledText(list_frame, height=8, wrap=tk.WORD)
        list_text.pack(fill=tk.BOTH, expand=True)
        
        for record_id, record_data in self.selected_records:
            record_type = record_data.get('type', '')
            name = record_data.get('name', '')
            content = record_data.get('content', '')
            list_text.insert(tk.END, f"{record_type} | {name} | {content}\n")
        
        list_text.config(state=tk.DISABLED)
        
        # 修改选项
        options_frame = ttk.LabelFrame(frame, text="修改选项", padding="10")
        options_frame.pack(fill=tk.X, pady=(0, 10))
        
        # TTL修改
        ttl_frame = ttk.Frame(options_frame)
        ttl_frame.pack(fill=tk.X, pady=5)
        
        self.change_ttl_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(ttl_frame, text="修改TTL为:", 
                       variable=self.change_ttl_var).pack(side=tk.LEFT)
        
        self.ttl_combo = ttk.Combobox(ttl_frame, width=15, state="readonly")
        self.ttl_combo['values'] = ('Auto', '120', '300', '600', '1800', '3600', '7200', '18000', '43200', '86400')
        self.ttl_combo.current(0)
        self.ttl_combo.pack(side=tk.LEFT, padx=(10, 0))
        
        # 代理修改
        proxy_frame = ttk.Frame(options_frame)
        proxy_frame.pack(fill=tk.X, pady=5)
        
        self.change_proxy_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(proxy_frame, text="修改代理状态为:", 
                       variable=self.change_proxy_var).pack(side=tk.LEFT)
        
        self.proxy_combo = ttk.Combobox(proxy_frame, width=15, state="readonly")
        self.proxy_combo['values'] = ('开启', '关闭')
        self.proxy_combo.current(0)
        self.proxy_combo.pack(side=tk.LEFT, padx=(10, 0))
        
        # 内容替换
        replace_frame = ttk.Frame(options_frame)
        replace_frame.pack(fill=tk.X, pady=5)
        
        self.replace_content_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(replace_frame, text="内容替换:", 
                       variable=self.replace_content_var).pack(side=tk.LEFT)
        
        ttk.Label(replace_frame, text="查找:").pack(side=tk.LEFT, padx=(10, 5))
        self.find_entry = ttk.Entry(replace_frame, width=15)
        self.find_entry.pack(side=tk.LEFT)
        
        ttk.Label(replace_frame, text="替换为:").pack(side=tk.LEFT, padx=(10, 5))
        self.replace_entry = ttk.Entry(replace_frame, width=15)
        self.replace_entry.pack(side=tk.LEFT)
        
        # 提示
        ttk.Label(options_frame, text="注意：只有A和AAAA记录支持代理功能", 
                 foreground="orange", font=('TkDefaultFont', 8)).pack(anchor=tk.W, pady=(5, 0))
        
        # 按钮
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=(10, 0))
        
        ttk.Button(btn_frame, text="开始修改", command=self.batch_edit).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def batch_edit(self):
        """批量修改DNS记录"""
        # 检查是否选择了任何修改选项
        if not (self.change_ttl_var.get() or self.change_proxy_var.get() or self.replace_content_var.get()):
            messagebox.showwarning("警告", "请至少选择一个修改选项")
            return
        
        # 确认
        modifications = []
        if self.change_ttl_var.get():
            modifications.append(f"TTL修改为 {self.ttl_combo.get()}")
        if self.change_proxy_var.get():
            modifications.append(f"代理状态修改为 {self.proxy_combo.get()}")
        if self.replace_content_var.get():
            modifications.append(f"内容替换：'{self.find_entry.get()}' → '{self.replace_entry.get()}'")
        
        confirm_msg = f"确定要对 {len(self.selected_records)} 条记录进行以下修改吗？\n\n" + "\n".join(modifications)
        
        if not messagebox.askyesno("确认", confirm_msg):
            return
        
        success_count = 0
        fail_count = 0
        results = []
        
        for record_id, record_data in self.selected_records:
            try:
                record_type = record_data.get('type')
                name = record_data.get('name')
                content = record_data.get('content')
                
                # 构建更新数据
                data = {
                    "type": record_type,
                    "name": name,
                    "content": content,
                    "ttl": record_data.get('ttl', 1),
                    "proxied": record_data.get('proxied', False)
                }
                
                # 应用修改
                modified = False
                
                # TTL修改
                if self.change_ttl_var.get():
                    ttl_str = self.ttl_combo.get()
                    data['ttl'] = 1 if ttl_str == 'Auto' else int(ttl_str)
                    modified = True
                
                # 代理修改
                if self.change_proxy_var.get():
                    if record_type not in ['A', 'AAAA', 'CNAME']:
                        results.append(f"[跳过] {record_type} {name}: 不支持代理")
                        continue
                    
                    data['proxied'] = self.proxy_combo.get() == '开启'
                    if data['proxied']:
                        data['ttl'] = 1  # 代理开启时TTL必须为1
                    modified = True
                
                # 内容替换
                if self.replace_content_var.get():
                    find_text = self.find_entry.get()
                    replace_text = self.replace_entry.get()
                    if find_text and find_text in content:
                        data['content'] = content.replace(find_text, replace_text)
                        modified = True
                
                if not modified:
                    results.append(f"[跳过] {record_type} {name}: 无需修改")
                    continue
                
                # 保留其他字段
                if record_data.get('priority') is not None:
                    data['priority'] = record_data.get('priority')
                
                # 发送更新请求
                result, error = self.api._request("PATCH", 
                                                 f"/zones/{self.zone_id}/dns_records/{record_id}", 
                                                 data)
                
                if error:
                    results.append(f"[失败] {record_type} {name}: {error}")
                    fail_count += 1
                else:
                    results.append(f"[成功] {record_type} {name}: 修改成功")
                    success_count += 1
                    
            except Exception as e:
                results.append(f"[错误] {name}: {str(e)}")
                fail_count += 1
        
        # 显示结果
        self.show_results(success_count, fail_count, results)
        
        if success_count > 0:
            self.success = True
    
    def show_results(self, success_count, fail_count, results):
        """显示批量操作结果"""
        result_dialog = tk.Toplevel(self.dialog)
        result_dialog.title("批量修改结果")
        result_dialog.geometry("900x500")
        result_dialog.transient(self.dialog)
        
        result_frame = ttk.Frame(result_dialog, padding="20")
        result_frame.pack(fill=tk.BOTH, expand=True)
        
        summary = f"成功: {success_count}, 失败: {fail_count}\n\n"
        ttk.Label(result_frame, text=summary, font=('TkDefaultFont', 10, 'bold')).pack(anchor=tk.W)
        
        result_text = scrolledtext.ScrolledText(result_frame, width=100, height=20)
        result_text.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        for line in results:
            result_text.insert(tk.END, line + '\n')
        
        result_text.config(state=tk.DISABLED)
        
        ttk.Button(result_frame, text="关闭", 
                  command=lambda: [result_dialog.destroy(), self.dialog.destroy()]).pack(pady=(10, 0))


class PendingDomainsDialog:
    """Pending状态域名列表对话框"""
    def __init__(self, parent, pending_domains):
        self.pending_domains = pending_domains
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"Pending状态域名列表 (共 {len(pending_domains)} 个)")
        self.dialog.geometry("900x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.setup_ui()
        
        # 居中显示
        center_window(self.dialog, parent)
    
    def setup_ui(self):
        """设置界面"""
        frame = ttk.Frame(self.dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(frame, 
                               text="以下域名处于 Pending 状态，请修改域名DNS服务器为Cloudflare名称服务器",
                               font=('TkDefaultFont', 10, 'bold'),
                               foreground="orange")
        title_label.pack(anchor=tk.W, pady=(0, 10))
        
        # 创建文本区域
        text_frame = ttk.Frame(frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        # 滚动文本框
        self.text_widget = scrolledtext.ScrolledText(text_frame, 
                                                     width=100, 
                                                     height=30,
                                                     wrap=tk.WORD,
                                                     font=('Consolas', 10))
        self.text_widget.pack(fill=tk.BOTH, expand=True)
        
        # 填充内容
        self.populate_content()
        
        # 设置为只读
        self.text_widget.config(state=tk.DISABLED)
        
        # 按钮
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=(10, 0))
        
        ttk.Button(btn_frame, text="复制全部", command=self.copy_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="导出到文件", command=self.export_to_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="关闭", command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def populate_content(self):
        """填充内容"""
        self.text_widget.config(state=tk.NORMAL)
        
        for i, domain_info in enumerate(self.pending_domains, 1):
            domain = domain_info['domain']
            nameservers = domain_info['nameservers']
            
            # 域名标题
            self.text_widget.insert(tk.END, f"{i}. {domain}\n", "domain")
            self.text_widget.insert(tk.END, "=" * 80 + "\n")
            
            # 名称服务器
            if nameservers:
                self.text_widget.insert(tk.END, "请将域名DNS服务器修改为:\n", "label")
                for j, ns in enumerate(nameservers, 1):
                    self.text_widget.insert(tk.END, f"   {j}. {ns}\n", "ns")
            else:
                self.text_widget.insert(tk.END, "   暂无名称服务器信息\n", "error")
            
            self.text_widget.insert(tk.END, "\n")
        
        # 配置标签样式
        self.text_widget.tag_config("domain", foreground="blue", font=('Consolas', 11, 'bold'))
        self.text_widget.tag_config("label", foreground="green")
        self.text_widget.tag_config("ns", foreground="black")
        self.text_widget.tag_config("error", foreground="red")
    
    def copy_all(self):
        """复制所有内容到剪贴板"""
        content = self.text_widget.get(1.0, tk.END)
        self.dialog.clipboard_clear()
        self.dialog.clipboard_append(content)
        messagebox.showinfo("成功", "已复制到剪贴板")
    
    def export_to_file(self):
        """导出到文件"""
        from tkinter import filedialog
        import datetime
        
        # 默认文件名
        default_name = f"pending_domains_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        filename = filedialog.asksaveasfilename(
            title="导出Pending域名列表",
            defaultextension=".txt",
            initialfile=default_name,
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        
        if filename:
            try:
                content = self.text_widget.get(1.0, tk.END)
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                messagebox.showinfo("成功", f"已导出到: {filename}")
            except Exception as e:
                messagebox.showerror("错误", f"导出失败: {str(e)}")


# ==================== 主窗口 ====================

class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Cloudflare DNS 域名管理工具 - 多账号版")
        self.root.geometry("1500x700")
        
        self.api = None
        self.current_zone = None
        self.zones_data = {}
        self.sort_column = None  # 当前排序列
        self.sort_reverse = False  # 排序方向
        self.available_accounts = []  # 可用的 Account ID 列表
        self.current_account_id = None  # 当前选择的 Account ID
        
        self.setup_ui()
        self.check_config()
    
    def setup_ui(self):
        """设置界面"""
        # 菜单栏
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 设置菜单
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="设置", menu=settings_menu)
        settings_menu.add_command(label="账号管理", command=self.show_account_manage)
        
        # 顶部工具栏
        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(toolbar, text="当前账号:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.account_label = ttk.Label(toolbar, text="未选择", foreground="blue", font=('TkDefaultFont', 9, 'bold'))
        self.account_label.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(toolbar, text="切换账号", command=self.show_account_manage).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="刷新", command=self.refresh_domains).pack(side=tk.LEFT, padx=2)
        
        # Account ID 下拉选择
        ttk.Label(toolbar, text="Account ID:").pack(side=tk.LEFT, padx=(15, 5))
        
        self.account_id_var = tk.StringVar()
        self.account_id_combo = ttk.Combobox(toolbar, textvariable=self.account_id_var, width=35, state="readonly")
        self.account_id_combo.pack(side=tk.LEFT, padx=2)
        self.account_id_combo.bind("<<ComboboxSelected>>", self.on_account_id_changed)
        
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 左侧：域名列表
        left_frame = ttk.LabelFrame(main_frame, text="域名列表", padding="5")
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        
        # 域名列表按钮
        domain_btn_frame = ttk.Frame(left_frame)
        domain_btn_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 5))
        
        ttk.Button(domain_btn_frame, text="刷新", command=self.refresh_domains).pack(side=tk.LEFT, padx=2)
        ttk.Button(domain_btn_frame, text="添加域名", command=self.show_add_domain_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(domain_btn_frame, text="批量添加", command=self.show_batch_add_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(domain_btn_frame, text="删除域名", command=self.delete_domain).pack(side=tk.LEFT, padx=2)
        ttk.Button(domain_btn_frame, text="Pending列表", command=self.show_pending_domains).pack(side=tk.LEFT, padx=2)
        ttk.Button(domain_btn_frame, text="导出域名", command=self.export_domains).pack(side=tk.LEFT, padx=2)
        
        # 域名列表
        self.domain_tree = ttk.Treeview(left_frame, columns=("domain", "status"), show="headings", height=15)
        self.domain_tree.heading("domain", text="域名", command=lambda: self.sort_domains("domain"))
        self.domain_tree.heading("status", text="状态", command=lambda: self.sort_domains("status"))
        self.domain_tree.column("domain", width=250, minwidth=150, stretch=True)
        self.domain_tree.column("status", width=80, minwidth=60, stretch=False)
        self.domain_tree.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.domain_tree.bind("<<TreeviewSelect>>", self.on_domain_select)
        
        # 垂直滚动条
        domain_scroll_y = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.domain_tree.yview)
        domain_scroll_y.grid(row=1, column=1, sticky=(tk.N, tk.S))
        self.domain_tree.configure(yscrollcommand=domain_scroll_y.set)
        
        # 横向滚动条
        domain_scroll_x = ttk.Scrollbar(left_frame, orient=tk.HORIZONTAL, command=self.domain_tree.xview)
        domain_scroll_x.grid(row=2, column=0, sticky=(tk.W, tk.E))
        self.domain_tree.configure(xscrollcommand=domain_scroll_x.set)
        
        # 名称服务器信息
        ns_frame = ttk.LabelFrame(left_frame, text="名称服务器", padding="5")
        ns_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))
        
        self.ns_text = scrolledtext.ScrolledText(ns_frame, height=8, width=30, wrap=tk.WORD)
        self.ns_text.pack(fill=tk.BOTH, expand=True)
        
        # 右侧：DNS记录
        right_frame = ttk.LabelFrame(main_frame, text="DNS记录", padding="5")
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # DNS记录按钮
        record_btn_frame = ttk.Frame(right_frame)
        record_btn_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        ttk.Button(record_btn_frame, text="刷新", command=self.refresh_records).pack(side=tk.LEFT, padx=2)
        ttk.Button(record_btn_frame, text="添加记录", command=self.show_add_record_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(record_btn_frame, text="批量添加", command=self.show_batch_add_records_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(record_btn_frame, text="修改记录", command=self.show_edit_record_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(record_btn_frame, text="批量修改", command=self.show_batch_edit_records_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(record_btn_frame, text="删除记录", command=self.delete_record).pack(side=tk.LEFT, padx=2)
        ttk.Button(record_btn_frame, text="开启代理", command=lambda: self.toggle_proxy(True)).pack(side=tk.LEFT, padx=2)
        ttk.Button(record_btn_frame, text="关闭代理", command=lambda: self.toggle_proxy(False)).pack(side=tk.LEFT, padx=2)
        ttk.Button(record_btn_frame, text="批量开启代理", command=lambda: self.batch_toggle_proxy(True)).pack(side=tk.LEFT, padx=2)
        ttk.Button(record_btn_frame, text="批量关闭代理", command=lambda: self.batch_toggle_proxy(False)).pack(side=tk.LEFT, padx=2)
        
        # DNS记录列表
        self.record_tree = ttk.Treeview(right_frame, 
                                        columns=("type", "name", "content", "proxy", "ttl"), 
                                        show="headings", 
                                        height=20)
        self.record_tree.heading("type", text="类型")
        self.record_tree.heading("name", text="名称")
        self.record_tree.heading("content", text="内容")
        self.record_tree.heading("proxy", text="代理")
        self.record_tree.heading("ttl", text="TTL")
        
        self.record_tree.column("type", width=80, minwidth=60, stretch=False)
        self.record_tree.column("name", width=250, minwidth=150, stretch=True)
        self.record_tree.column("content", width=250, minwidth=150, stretch=True)
        self.record_tree.column("proxy", width=60, minwidth=50, stretch=False)
        self.record_tree.column("ttl", width=80, minwidth=60, stretch=False)
        
        self.record_tree.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 垂直滚动条
        record_scroll_y = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.record_tree.yview)
        record_scroll_y.grid(row=1, column=1, sticky=(tk.N, tk.S))
        self.record_tree.configure(yscrollcommand=record_scroll_y.set)
        
        # 横向滚动条
        record_scroll_x = ttk.Scrollbar(right_frame, orient=tk.HORIZONTAL, command=self.record_tree.xview)
        record_scroll_x.grid(row=2, column=0, sticky=(tk.W, tk.E))
        self.record_tree.configure(xscrollcommand=record_scroll_x.set)
        
        # 配置权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=2)
        main_frame.rowconfigure(0, weight=1)
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(1, weight=1)
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(1, weight=1)
    
    def update_account_label(self):
        """更新账号标签"""
        account = config.get_current_account()
        if account:
            self.account_label.config(text=account['name'])
        else:
            self.account_label.config(text="未选择")
    
    def load_account_ids(self):
        """加载可用的 Account ID 列表"""
        if not self.api:
            return
        
        # 获取账号列表
        result, error = self.api.get_accounts()
        
        if error or not result:
            # 如果获取失败，使用配置中的 account_id
            account = config.get_current_account()
            if account and account.get('account_id'):
                self.available_accounts = [
                    {
                        'id': account.get('account_id'),
                        'name': f"{account['name']} (配置)"
                    }
                ]
            else:
                self.available_accounts = [{'id': '', 'name': '所有账号'}]
        else:
            # 成功获取账号列表
            # result 是元组 (data, error)，data 可能是字典或列表
            if isinstance(result, dict):
                accounts = result.get('result', [])
            elif isinstance(result, list):
                accounts = result
            else:
                accounts = []
            
            self.available_accounts = [{'id': '', 'name': '所有账号'}]  # 添加"所有账号"选项
            
            for acc in accounts:
                if isinstance(acc, dict):
                    self.available_accounts.append({
                        'id': acc.get('id', ''),
                        'name': f"{acc.get('name', '未命名')} ({acc.get('id', '')[:8]}...)"
                    })
        
        # 更新下拉菜单
        self.update_account_id_combo()
    
    def update_account_id_combo(self):
        """更新 Account ID 下拉菜单"""
        if not self.available_accounts:
            self.account_id_combo['values'] = ['所有账号']
            self.account_id_var.set('所有账号')
            return
        
        # 设置下拉菜单选项
        values = [acc['name'] for acc in self.available_accounts]
        self.account_id_combo['values'] = values
        
        # 设置当前选择
        if self.current_account_id:
            # 查找当前 account_id 对应的显示名称
            for acc in self.available_accounts:
                if acc['id'] == self.current_account_id:
                    self.account_id_var.set(acc['name'])
                    return
        
        # 默认选择第一个（所有账号）
        if values:
            self.account_id_var.set(values[0])
    
    def on_account_id_changed(self, event=None):
        """Account ID 选择改变事件"""
        selected_name = self.account_id_var.get()
        
        # 查找对应的 account_id
        for acc in self.available_accounts:
            if acc['name'] == selected_name:
                self.current_account_id = acc['id']
                break
        
        # 刷新域名列表
        self.refresh_domains()
    
    def check_config(self):
        """检查配置"""
        if not config.is_configured():
            self.show_account_manage()
        else:
            account = config.get_current_account()
            if account:
                self.api = CloudflareAPI(
                    account['api_token'], 
                    account.get('account_id', ''),
                    account.get('email', ''),
                    account.get('auth_type', 'token')
                )
                self.update_account_label()
                self.load_account_ids()  # 加载 Account ID 列表
                self.refresh_domains()
    
    def show_account_manage(self):
        """显示账号管理对话框"""
        dialog = AccountManageDialog(self.root)
        self.root.wait_window(dialog.dialog)
        
        # 刷新当前账号
        account = config.get_current_account()
        if account:
            self.api = CloudflareAPI(
                account['api_token'], 
                account.get('account_id', ''),
                account.get('email', ''),
                account.get('auth_type', 'token')
            )
            self.update_account_label()
            self.load_account_ids()  # 加载 Account ID 列表
            self.refresh_domains()
    
    def refresh_domains(self):
        """刷新域名列表"""
        if not self.api:
            messagebox.showwarning("警告", "请先配置账号")
            return
        
        # 清空列表
        for item in self.domain_tree.get_children():
            self.domain_tree.delete(item)
        
        self.zones_data.clear()
        
        # 显示加载提示
        loading_id = self.domain_tree.insert("", tk.END, values=("正在加载域名列表...", ""))
        self.root.update()
        
        # 获取域名列表 - 使用当前选择的 Account ID
        # 如果 current_account_id 为空字符串，表示"所有账号"
        zones, error = self.api.get_zones(self.current_account_id if self.current_account_id else None)
        
        # 删除加载提示
        self.domain_tree.delete(loading_id)
        
        if error:
            messagebox.showerror("错误", f"获取域名列表失败: {error}")
            return
        
        # 填充列表
        if zones:
            for zone in zones:
                zone_id = zone['id']
                domain = zone['name']
                status = zone['status']
                
                self.zones_data[zone_id] = zone
                self.domain_tree.insert("", tk.END, iid=zone_id, values=(domain, status))
            
            # 显示统计信息
            self.root.title(f"Cloudflare DNS 域名管理工具 - 多账号版 ({len(zones)} 个域名)")
        else:
            self.root.title("Cloudflare DNS 域名管理工具 - 多账号版")
    
    def sort_domains(self, column):
        """排序域名列表"""
        # 如果点击相同的列，则反转排序顺序
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column
            self.sort_reverse = False
        
        # 获取所有项目
        items = []
        for item_id in self.domain_tree.get_children():
            values = self.domain_tree.item(item_id)['values']
            items.append((item_id, values))
        
        # 根据选择的列排序
        if column == "domain":
            items.sort(key=lambda x: x[1][0].lower(), reverse=self.sort_reverse)
        elif column == "status":
            # 状态排序：pending -> active -> 其他
            status_priority = {"pending": 0, "active": 1}
            items.sort(
                key=lambda x: (status_priority.get(x[1][1], 2), x[1][1].lower()),
                reverse=self.sort_reverse
            )
        
        # 重新插入项目
        for index, (item_id, values) in enumerate(items):
            self.domain_tree.move(item_id, "", index)
        
        # 更新列标题显示排序方向
        arrow = " ↓" if self.sort_reverse else " ↑"
        if column == "domain":
            self.domain_tree.heading("domain", text=f"域名{arrow}")
            self.domain_tree.heading("status", text="状态")
        else:
            self.domain_tree.heading("domain", text="域名")
            self.domain_tree.heading("status", text=f"状态{arrow}")
    
    def show_pending_domains(self):
        """显示所有pending状态的域名"""
        if not self.api:
            messagebox.showwarning("警告", "请先配置账号")
            return
        
        # 收集pending域名
        pending_domains = []
        for zone_id, zone in self.zones_data.items():
            if zone.get('status') == 'pending':
                domain_name = zone.get('name')
                name_servers = zone.get('name_servers', [])
                
                # 如果没有名称服务器信息，尝试获取
                if not name_servers:
                    ns_list, error = self.api.get_zone_nameservers(zone_id)
                    if not error and ns_list:
                        name_servers = ns_list
                        zone['name_servers'] = ns_list
                
                pending_domains.append({
                    'domain': domain_name,
                    'nameservers': name_servers
                })
        
        if not pending_domains:
            messagebox.showinfo("提示", "没有pending状态的域名")
            return
        
        # 创建对话框显示pending域名
        PendingDomainsDialog(self.root, pending_domains)
    
    def export_domains(self):
        """导出所有域名到文本文件"""
        if not self.zones_data:
            messagebox.showwarning("警告", "当前没有域名可以导出")
            return
        
        # 从文件对话框获取保存路径
        from tkinter import filedialog
        import datetime
        
        # 默认文件名：域名列表_日期时间.txt
        default_filename = f"域名列表_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        filepath = filedialog.asksaveasfilename(
            parent=self.root,
            title="导出域名列表",
            defaultextension=".txt",
            initialfile=default_filename,
            filetypes=[
                ("文本文件", "*.txt"),
                ("所有文件", "*.*")
            ]
        )
        
        if not filepath:
            return  # 用户取消
        
        try:
            # 收集所有域名
            domains = []
            for zone_id, zone in self.zones_data.items():
                domain_name = zone.get('name')
                if domain_name:
                    domains.append(domain_name)
            
            # 排序
            domains.sort()
            
            # 写入文件
            with open(filepath, 'w', encoding='utf-8') as f:
                for domain in domains:
                    f.write(domain + '\n')
            
            messagebox.showinfo("成功", 
                              f"成功导出 {len(domains)} 个域名到:\n{filepath}")
        
        except Exception as e:
            messagebox.showerror("错误", f"导出失败: {str(e)}")
    
    def on_domain_select(self, event):
        """域名选择事件"""
        selection = self.domain_tree.selection()
        if not selection:
            return
        
        zone_id = selection[0]
        self.current_zone = zone_id
        
        # 显示名称服务器
        self.show_nameservers(zone_id)
        
        # 刷新DNS记录
        self.refresh_records()
    
    def show_nameservers(self, zone_id):
        """显示名称服务器"""
        self.ns_text.delete(1.0, tk.END)
        
        if zone_id in self.zones_data:
            zone = self.zones_data[zone_id]
            name_servers = zone.get('name_servers', [])
            
            if name_servers:
                domain_name = zone.get('name', '')
                self.ns_text.insert(tk.END, f"域名: {domain_name}\n\n")
                self.ns_text.insert(tk.END, "请将域名的DNS服务器更改为:\n\n")
                for i, ns in enumerate(name_servers, 1):
                    self.ns_text.insert(tk.END, f"{i}. {ns}\n")
                
                self.ns_text.insert(tk.END, f"\n共 {len(name_servers)} 个名称服务器")
            else:
                # 如果zones_data中没有，尝试重新获取
                ns_list, error = self.api.get_zone_nameservers(zone_id)
                if error:
                    self.ns_text.insert(tk.END, f"获取名称服务器失败: {error}")
                elif ns_list:
                    domain_name = zone.get('name', '')
                    self.ns_text.insert(tk.END, f"域名: {domain_name}\n\n")
                    self.ns_text.insert(tk.END, "请将域名的DNS服务器更改为:\n\n")
                    for i, ns in enumerate(ns_list, 1):
                        self.ns_text.insert(tk.END, f"{i}. {ns}\n")
                    
                    self.ns_text.insert(tk.END, f"\n共 {len(ns_list)} 个名称服务器")
                    
                    # 更新缓存
                    zone['name_servers'] = ns_list
                else:
                    self.ns_text.insert(tk.END, "暂无名称服务器信息")
        else:
            self.ns_text.insert(tk.END, "请先选择域名")
    
    def refresh_records(self):
        """刷新DNS记录"""
        if not self.current_zone:
            return
        
        # 清空列表
        for item in self.record_tree.get_children():
            self.record_tree.delete(item)
        
        # 获取DNS记录
        records, error = self.api.list_dns_records(self.current_zone)
        if error:
            messagebox.showerror("错误", f"获取DNS记录失败: {error}")
            return
        
        # 填充列表
        if records:
            for record in records:
                record_id = record['id']
                record_type = record['type']
                name = record['name']
                content = record['content']
                proxied = "是" if record.get('proxied') else "否"
                ttl = record['ttl']
                
                self.record_tree.insert("", tk.END, iid=record_id, 
                                      values=(record_type, name, content, proxied, ttl))
    
    def show_add_domain_dialog(self):
        """显示添加域名对话框"""
        if not self.api:
            messagebox.showwarning("警告", "请先配置账号")
            return
        
        dialog = AddDomainDialog(self.root, self.api)
        self.root.wait_window(dialog.dialog)
        
        if dialog.success:
            self.refresh_domains()
    
    def show_batch_add_dialog(self):
        """显示批量添加域名对话框"""
        if not self.api:
            messagebox.showwarning("警告", "请先配置账号")
            return
        
        dialog = BatchAddDialog(self.root, self.api)
        self.root.wait_window(dialog.dialog)
        
        if dialog.success:
            self.refresh_domains()
    
    def delete_domain(self):
        """删除域名"""
        if not self.current_zone:
            messagebox.showwarning("警告", "请先选择域名")
            return
        
        zone = self.zones_data.get(self.current_zone)
        if not zone:
            return
        
        if not messagebox.askyesno("确认", f"确定要删除域名 {zone['name']} 吗?"):
            return
        
        result, error = self.api.delete_zone(self.current_zone)
        if error:
            messagebox.showerror("错误", f"删除域名失败: {error}")
        else:
            messagebox.showinfo("成功", "域名删除成功")
            self.current_zone = None
            self.refresh_domains()
    
    def show_add_record_dialog(self):
        """显示添加DNS记录对话框"""
        if not self.current_zone:
            messagebox.showwarning("警告", "请先选择域名")
            return
        
        dialog = AddRecordDialog(self.root, self.api, self.current_zone)
        self.root.wait_window(dialog.dialog)
        
        if dialog.success:
            self.refresh_records()
    
    def show_edit_record_dialog(self):
        """显示修改DNS记录对话框"""
        selection = self.record_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要修改的DNS记录")
            return
        
        if len(selection) > 1:
            messagebox.showwarning("警告", "一次只能修改一条记录")
            return
        
        record_id = selection[0]
        dialog = EditRecordDialog(self.root, self.api, self.current_zone, record_id)
        self.root.wait_window(dialog.dialog)
        
        if dialog.success:
            self.refresh_records()
    
    def show_batch_add_records_dialog(self):
        """显示批量添加DNS记录对话框"""
        if not self.current_zone:
            messagebox.showwarning("警告", "请先选择域名")
            return
        
        dialog = BatchAddRecordsDialog(self.root, self.api, self.current_zone)
        self.root.wait_window(dialog.dialog)
        
        if dialog.success:
            self.refresh_records()
    
    def show_batch_edit_records_dialog(self):
        """显示批量修改DNS记录对话框"""
        selection = self.record_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要修改的DNS记录")
            return
        
        # 获取选中记录的详细信息
        selected_records = []
        for record_id in selection:
            # 通过API获取记录详情
            result, error = self.api._request("GET", f"/zones/{self.current_zone}/dns_records/{record_id}")
            if not error and result:
                selected_records.append((record_id, result))
        
        if not selected_records:
            messagebox.showerror("错误", "无法获取选中记录的信息")
            return
        
        dialog = BatchEditRecordsDialog(self.root, self.api, self.current_zone, selected_records)
        self.root.wait_window(dialog.dialog)
        
        if dialog.success:
            self.refresh_records()
    
    def delete_record(self):
        """删除DNS记录"""
        selection = self.record_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择DNS记录")
            return
        
        if not messagebox.askyesno("确认", "确定要删除选中的DNS记录吗?"):
            return
        
        for record_id in selection:
            result, error = self.api.delete_dns_record(self.current_zone, record_id)
            if error:
                messagebox.showerror("错误", f"删除DNS记录失败: {error}")
                return
        
        messagebox.showinfo("成功", "DNS记录删除成功")
        self.refresh_records()
    
    def toggle_proxy(self, enable):
        """切换代理状态"""
        selection = self.record_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择DNS记录")
            return
        
        record_id = selection[0]
        result, error = self.api.update_record_proxy_status(self.current_zone, record_id, enable)
        
        if error:
            messagebox.showerror("错误", f"更新代理状态失败: {error}")
        else:
            status = "开启" if enable else "关闭"
            messagebox.showinfo("成功", f"代理已{status}")
            self.refresh_records()
    
    def batch_toggle_proxy(self, enable):
        """批量切换代理状态"""
        selection = self.record_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择DNS记录")
            return
        
        status = "开启" if enable else "关闭"
        if not messagebox.askyesno("确认", f"确定要批量{status}代理吗?"):
            return
        
        success_count = 0
        fail_count = 0
        
        for record_id in selection:
            result, error = self.api.update_record_proxy_status(self.current_zone, record_id, enable)
            if error:
                fail_count += 1
            else:
                success_count += 1
        
        messagebox.showinfo("完成", f"成功: {success_count}, 失败: {fail_count}")
        self.refresh_records()


# ==================== 程序入口 ====================

def main():
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()

if __name__ == "__main__":
    main()
