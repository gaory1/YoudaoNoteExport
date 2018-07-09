# YoudaoNoteExport
导出有道云笔记，保存为JSON和DOCX/XML文件。DOCX/XML文件是笔记的内容，JSON文件是笔记的其它信息（包括标题、创建时间、修改时间等）

使用方法：

python main.py 用户名 密码 [存盘目录 [文件类型]]

文件类型是xml（默认）或docx


举例：

mkdir notes

python main.py 用户名 密码 ./notes docx


在Ubuntu 16.04 + Python 2.7的环境中测试通过。
