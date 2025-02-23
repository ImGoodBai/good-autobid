import os
from pathlib import Path

def init_project():
    # 获取项目根目录
    base_dir = Path(__file__).parent.parent
    
    # 需要创建的目录
    directories = [
        base_dir / "inputs",
        base_dir / "outputs" / "outline",
        base_dir / "logs"
    ]
    
    # 需要创建的文件
    files = [
        base_dir / "inputs" / "tech.md",
        base_dir / "inputs" / "score.md",
        base_dir / "outputs" / "outline" / "outline.json",
        base_dir / "outputs" / "outline" / "outline.md",
        base_dir / "logs" / "app.log"
    ]
    
    # 创建目录
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")
    
    # 创建文件
    for file in files:
        if not file.exists():
            file.touch()
            print(f"Created file: {file}")
    
    # 如果存在旧的tech.md和score.md，移动它们到新位置
    old_tech = base_dir / "bidding" / "tech.md"
    old_score = base_dir / "bidding" / "score.md"
    
    if old_tech.exists():
        with old_tech.open('r', encoding='utf-8') as f:
            content = f.read()
        with (base_dir / "inputs" / "tech.md").open('w', encoding='utf-8') as f:
            f.write(content)
        old_tech.unlink()
        print("Moved tech.md to inputs directory")
    
    if old_score.exists():
        with old_score.open('r', encoding='utf-8') as f:
            content = f.read()
        with (base_dir / "inputs" / "score.md").open('w', encoding='utf-8') as f:
            f.write(content)
        old_score.unlink()
        print("Moved score.md to inputs directory")

if __name__ == "__main__":
    init_project() 