import datetime
import llm
import file
import sys
import argparse
from openai import OpenAI

def create_llm_instance():
    """创建LLM实例"""
    config = file.read_config()
    if not config:
        print("未找到配置文件，请先配置大模型设置")
        return None
    
    llms = config.get('llms', [])
    default_llm = config.get('default_llm', '')
    
    # 查找默认的LLM配置
    selected_llm = None
    for llm_config in llms:
        if llm_config.get('name') == default_llm:
            selected_llm = llm_config
            break
    
    if not selected_llm:
        print(f"未找到默认LLM配置: {default_llm}")
        return None
    
    try:
        client = OpenAI(
            api_key=selected_llm['api_key'],
            base_url=selected_llm['base_url']
        )
        return llm.LLM(
            client=client,
            model=selected_llm['model'],
            temperature=selected_llm['temperature'],
            sys_prompt=""
        )
    except Exception as e:
        print(f"创建LLM实例失败: {e}")
        return None

def chat_loop(instance:llm.LLM):
    """无限循环聊天"""
    if not instance:
        return
    
    print(r"开始聊天模式，输入 \quit(\q) 或 \exit(\e) 退出")
    print("=" * 50)
    
    while True:
        try:
            user_input = input("\n>>> ")
            if user_input.lower() in ['\\q', '\\e','\\quit','\\exit']:
                print("再见！")
                break
            if user_input.strip():
                instance.chat(user_input)
        except KeyboardInterrupt:
            print("\n\n再见！")
            break
        except Exception as e:
            print(f"聊天出错: {e}")
            break


def add_llm_config(config):
    """添加新的LLM配置"""
    print("添加新的LLM配置")
    print("需要配置的选项有: name, api_key, base_url, model, temperature")
    print("-" * 30)
    
    print('name 仅用于标识，不影响实际使用。默认值为月份+日期')
    name = input("name: ").strip()
    if not name:
        from datetime import datetime
        name = datetime.now().strftime('%m%d')
    print(f'{name = }')
    
    api_key = input("API Key: ").strip()
    if not api_key:
        print("API Key不能为空")
        return config
    # print(f'{api_key = }')
    
    base_url = input("Base URL (默认: https://api.openai.com/v1): ").strip()
    if not base_url:
        base_url = "https://api.openai.com/v1"
    print(f'{base_url = }')
    
    model = input("模型名称: ").strip()
    if not model:
        print("模型名称不能为空")
        return config
    
    try:
        temperature = float(input("Temperature (0.0-2.0, 默认: 0.7): ").strip() or "0.7")
        if not 0.0 <= temperature <= 2.0:
            print("Temperature必须在0.0-2.0之间")
            return config
    except ValueError:
        print("Temperature必须是数字")
        return config
    print(f'{temperature = }')
    
    # 检查是否已存在同名配置
    for i, llm_config in enumerate(config['llms']):
        if llm_config.get('name') == name:
            print(f"配置 '{name}' 已存在，是否覆盖？(y/N)")
            if input().lower() != 'y':
                return config
            config['llms'][i] = {
                'name':name,
                'api_key': api_key,
                'base_url': base_url,
                'model': model,
                'temperature': temperature
            }
            print(f"配置 '{name}' 更新成功！")
            return config
    
    # 添加新配置
    config['llms'].append({
        'name': name,
        'api_key': api_key,
        'base_url': base_url,
        'model': model,
        'temperature': temperature
    })
    
    # 如果是第一个配置，设为默认
    if not config['default_llm']:
        config['default_llm'] = name
    
    print(f"配置 '{name}' 添加成功！")
    return config

def list_llm_configs(config):
    """列出所有LLM配置"""
    if not config:
        print("未找到任何配置")
        return config
    
    llms = config.get('llms', [])
    default_llm = config.get('default_llm', '')
    
    if not llms:
        print("未找到任何LLM配置")
        return config
    
    print("当前LLM配置:")
    print("-" * 50)
    for i, llm_config in enumerate(llms, 1):
        name = llm_config.get('name', f'配置{i}')
        model = llm_config.get('model', '未知')
        base_url = llm_config.get('base_url', '未知')
        temperature = llm_config.get('temperature', 0.7)
        is_default = " (默认)" if name == default_llm else ""
        print(f"{i}. {name}{is_default}")
        print(f"   模型: {model}")
        print(f"   Base URL: {base_url}")
        print(f"   Temperature: {temperature}")
        print()
    
    return config

def update_llm_config(config):
    """更新LLM配置"""
    if not config:
        print("未找到任何配置")
        return config
    
    llms = config.get('llms', [])
    if not llms:
        print("未找到任何LLM配置")
        return config
    
    print("选择要更新的配置:")
    for i, llm_config in enumerate(llms, 1):
        name = llm_config.get('name', f'配置{i}')
        model = llm_config.get('model', '未知')
        print(f"{i}. {name} ({model})")
    
    try:
        choice = int(input("请输入配置编号: ")) - 1
        if not 0 <= choice < len(llms):
            print("无效的配置编号")
            return config
    except ValueError:
        print("请输入有效的数字")
        return config
    
    selected_config = llms[choice]
    print(f"\n更新配置: {selected_config.get('name', f'配置{choice+1}')}")
    print("直接回车保持原值")
    
    # 只允许更新除 name 以外的字段
    new_api_key = input(f"API Key [***]: ").strip()
    if new_api_key:
        selected_config['api_key'] = new_api_key
    
    new_base_url = input(f"Base URL [{selected_config.get('base_url', '')}]: ").strip()
    if new_base_url:
        selected_config['base_url'] = new_base_url
    
    new_model = input(f"模型名称 [{selected_config.get('model', '')}]: ").strip()
    if new_model:
        selected_config['model'] = new_model
    
    new_temp = input(f"Temperature [{selected_config.get('temperature', 0.7)}]: ").strip()
    if new_temp:
        try:
            temperature = float(new_temp)
            if 0.0 <= temperature <= 2.0:
                selected_config['temperature'] = temperature
            else:
                print("Temperature必须在0.0-2.0之间，保持原值")
        except ValueError:
            print("Temperature必须是数字，保持原值")
    
    print("配置已更新")
    return config

def delete_llm_config(config):
    """删除LLM配置"""
    if not config:
        print("未找到任何配置")
        return config
    
    llms = config.get('llms', [])
    if not llms:
        print("未找到任何LLM配置")
        return config
    
    print("选择要删除的配置:")
    for i, llm_config in enumerate(llms, 1):
        name = llm_config.get('name', f'配置{i}')
        model = llm_config.get('model', '未知')
        is_default = " (默认)" if name == config.get('default_llm', '') else ""
        print(f"{i}. {name}{is_default} ({model})")
    
    try:
        choice = int(input("请输入配置编号: ")) - 1
        if not 0 <= choice < len(llms):
            print("无效的配置编号")
            return config
    except ValueError:
        print("请输入有效的数字")
        return config
    
    selected_config = llms[choice]
    name = selected_config.get('name', f'配置{choice+1}')
    
    print(f"\n确定要删除配置 '{name}' 吗？(y/N)")
    if input().lower() != 'y':
        print("取消删除")
        return config
    
    # 如果删除的是默认配置，需要重新设置默认配置
    if name == config.get('default_llm', ''):
        config['default_llm'] = ''
        if len(llms) > 1:
            remaining_configs = [c for c in llms if c != selected_config]
            if remaining_configs:
                config['default_llm'] = remaining_configs[0].get('name', '')
    
    llms.remove(selected_config)
    print(f"配置 '{name}' 删除成功！")
    return config

def set_default_llm(config):
    """设置默认LLM"""
    if not config:
        print("未找到任何配置")
        return config
    
    llms = config.get('llms', [])
    if not llms:
        print("未找到任何LLM配置")
        return config
    
    print("选择默认LLM:")
    for i, llm_config in enumerate(llms, 1):
        name = llm_config.get('name', f'配置{i}')
        model = llm_config.get('model', '未知')
        is_default = " (当前默认)" if name == config.get('default_llm', '') else ""
        print(f"{i}. {name}{is_default} ({model})")
    
    try:
        choice = int(input("请输入配置编号: ")) - 1
        if not 0 <= choice < len(llms):
            print("无效的配置编号")
            return config
    except ValueError:
        print("请输入有效的数字")
        return config
    
    selected_config = llms[choice]
    name = selected_config.get('name', f'配置{choice+1}')
    
    config['default_llm'] = name
    print(f"默认LLM已设置为: {name}")
    return config

# 命令字典
COMMANDS = {
    'add': add_llm_config,
    'list': list_llm_configs,
    'update': update_llm_config,
    'delete': delete_llm_config,
    'default': set_default_llm,
}

def main():
    """主函数"""
    if len(sys.argv) == 1:
        instance = create_llm_instance()
        chat_loop(instance)
    else:
        # 有参数，解析命令
        parser = argparse.ArgumentParser(
            description='GG CLI - 大模型命令行工具',
            epilog="""
使用示例:
  gg                    # 启动交互式聊天模式
  gg "你好"             # 发送单条消息并退出
  gg add                # 添加新的LLM配置
  gg list               # 查看所有LLM配置
  gg update             # 更新现有LLM配置
  gg delete             # 删除LLM配置
  gg default            # 设置默认LLM

聊天模式退出命令:
  \\q, \\e, \\quit, \\exit  # 退出聊天模式

            """,
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        subparsers = parser.add_subparsers(
            dest='command', 
            help='可用命令 (不区分大小写)',
            metavar='COMMAND'
        )
        
        # 添加配置
        add_parser = subparsers.add_parser(
            'add', 
            help='添加新的LLM配置',
            description='交互式添加新的LLM配置。如果配置名称已存在，会询问是否覆盖。'
        )
        add_parser.epilog = """
配置项说明:
  name        - 配置标识名称，仅用于管理，不影响实际使用
  api_key     - 大模型API密钥，必需
  base_url    - API基础URL，默认为OpenAI官方地址
  model       - 模型名称，必需
  temperature - 温度参数(0.0-2.0)，控制输出随机性，默认0.7

注意: 如果是第一个配置，会自动设为默认配置。
        """
        
        # 列出配置
        list_parser = subparsers.add_parser(
            'list', 
            help='查看所有LLM配置',
            description='显示所有已保存的LLM配置信息，包括默认配置标识。'
        )
        list_parser.epilog = """
显示信息包括:
  - 配置名称和编号
  - 是否为默认配置
  - 模型名称
  - API基础URL
  - 温度参数
        """
        
        # 更新配置
        update_parser = subparsers.add_parser(
            'update', 
            help='更新现有LLM配置',
            description='交互式更新现有LLM配置。只能更新除名称外的其他字段。'
        )
        update_parser.epilog = """
可更新字段:
  api_key     - API密钥
  base_url    - API基础URL
  model       - 模型名称
  temperature - 温度参数

注意: 配置名称不可修改，如需修改请删除后重新添加。
        """
        
        # 删除配置
        delete_parser = subparsers.add_parser(
            'delete', 
            help='删除LLM配置',
            description='删除指定的LLM配置。删除前会要求确认。'
        )
        delete_parser.epilog = """
删除规则:
  - 删除默认配置时，会自动将其他配置中的第一个设为默认
  - 如果只有一个配置，删除后默认配置将为空
  - 删除操作不可撤销，请谨慎操作
        """
        
        # 设置默认LLM
        default_parser = subparsers.add_parser(
            'default', 
            help='设置默认LLM',
            description='从现有配置中选择一个设为默认LLM。'
        )
        default_parser.epilog = """
默认LLM说明:
  - 启动聊天模式时使用默认LLM
  - 发送单条消息时使用默认LLM
  - 必须至少有一个配置才能设置默认LLM
        """
        
        args = parser.parse_args()
        
        # 不区分大小写的命令匹配
        command = args.command.lower() if args.command else None
        
        if command in COMMANDS:
            # 读取配置
            config = file.read_config()
            if not config:
                config = {"llms": [], "default_llm": ""}
            
            # 执行命令
            updated_config = COMMANDS[command](config)
            
            # 保存配置
            file.save_config(updated_config)
        elif command.strip('\'" \n\r') in {'help','/help','-help','--help','h','/h','-h','--h'}:
            parser.print_help()
        else:
            instance = create_llm_instance()
            instance.chat(sys.argv[1].strip('" '))

if __name__ == '__main__':
    main()
