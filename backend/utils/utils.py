"""本代码获取root路径的代码由大模型生成，仅仅使用方法：
    get_project_root("backend") 其他的都可以删了"""


import os
import pathlib
import platform


def get_project_root(target_folder: str = "backend") -> pathlib.Path:
    """
    获取项目根目录路径
    
    自动检测操作系统并查找指定的目标文件夹作为项目根目录。
    从当前文件位置开始向上遍历，直到找到目标文件夹或到达文件系统根目录。
    
    Args:
        target_folder: 目标文件夹名称，默认为 "backend"
    
    Returns:
        pathlib.Path: 项目根目录的绝对路径
    
    Raises:
        RuntimeError: 如果无法找到目标文件夹
    
    Examples:
        >>> root = get_project_root("backend")
        >>> print(root)
        D:\WorkSpace\Projects\Refantastic\backend  # Windows
        /home/user/Projects/Refantastic/backend    # Linux
    """
    # 检测操作系统
    system = platform.system()
    is_windows = system == "Windows"
    is_linux = system == "Linux"
    is_mac = system == "Darwin"
    
    print(f"当前操作系统: {system}")
    print(f"路径分隔符: {os.sep}")
    
    # 获取当前文件的绝对路径
    current_path = pathlib.Path(__file__).resolve()
    print(f"当前文件路径: {current_path}")
    
    # 从当前目录开始向上查找
    search_path = current_path.parent
    max_iterations = 10  # 防止无限循环
    iteration = 0
    
    while iteration < max_iterations:
        # 获取当前目录名称
        current_folder = search_path.name
        print(f"检查目录: {search_path} (文件夹名: {current_folder})")
        
        # 检查是否为目标文件夹
        if current_folder == target_folder:
            print(f"找到项目根目录: {search_path}")
            return search_path
        
        # 检查是否已到达文件系统根目录
        parent = search_path.parent
        if parent == search_path:
            # 已到达根目录
            raise RuntimeError(
                f"无法找到目标文件夹 '{target_folder}'。"
                f"已搜索至文件系统根目录。"
            )
        
        # 向上移动一级目录
        search_path = parent
        iteration += 1
    
    raise RuntimeError(
        f"查找目标文件夹 '{target_folder}' 超过最大迭代次数 ({max_iterations})。"
    )


def get_project_base(root_folder: str = "Refantastic") -> pathlib.Path:
    """
    获取项目基础目录（包含 backend 和 frontend 的父目录）
    
    Args:
        root_folder: 项目根文件夹名称，默认为 "Refantastic"
    
    Returns:
        pathlib.Path: 项目基础目录的绝对路径
    """
    return get_project_root(root_folder)


def ensure_directory_exists(path: pathlib.Path) -> pathlib.Path:
    """
    确保目录存在，如果不存在则创建
    
    Args:
        path: 目录路径
    
    Returns:
        pathlib.Path: 目录路径
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_data_dir(create: bool = True) -> pathlib.Path:
    """
    获取数据目录路径
    
    Args:
        create: 是否创建目录（如果不存在）
    
    Returns:
        pathlib.Path: 数据目录路径
    """
    backend_root = get_project_root("backend")
    data_dir = backend_root / "scripts" / "data"
    
    if create:
        ensure_directory_exists(data_dir)
    
    return data_dir


def normalize_path(path: str | pathlib.Path) -> pathlib.Path:
    """
    规范化路径，处理不同操作系统的路径格式
    
    Args:
        path: 输入路径
    
    Returns:
        pathlib.Path: 规范化后的路径对象
    """
    return pathlib.Path(path).resolve()


# 测试代码
if __name__ == "__main__":
    print("=" * 60)
    print("路径工具测试")
    print("=" * 60)
    
    try:
        # 测试获取 backend 根目录
        backend_root = get_project_root("backend")
        print(f"\nbackend 根目录: {backend_root}")
        
        # 测试获取项目基础目录
        project_base = get_project_base("Refantastic")
        print(f"项目基础目录: {project_base}")
        
        # 测试获取数据目录
        data_dir = get_data_dir(create=False)
        print(f"数据目录: {data_dir}")
        print(f"数据目录是否存在: {data_dir.exists()}")
        
        # 测试路径规范化
        test_path = "scripts/data/test.db"
        normalized = normalize_path(test_path)
        print(f"\n原始路径: {test_path}")
        print(f"规范化路径: {normalized}")
        
    except RuntimeError as e:
        print(f"\n错误: {e}")