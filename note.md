```py
json_schema 预先写死
json_object 只要是json格式就行


json   python
object->dict
array->list
string->str
number->int/float
boolean->bool
null->none

{"role": "system", "content": "你可以调用工具来完成用户请求；不需要工具时直接回答。"}
若不设置，ai会乱调工具

messages.append(msg) 让模型知道调用了什么
messages.append({"role":"tool","tool_call_id":msg.tool_calls[0].id,"content":result}) 让模型知道结果是什么

print(resp.model_dump_json(indent=2))

若调用工具有误，错误信息也应返回模型，让它调整参数

对工具的描述应该精准，不可模糊

description:
文件路径->文件的绝对/相对路径
读取文件->读取当前目录下的文件
```