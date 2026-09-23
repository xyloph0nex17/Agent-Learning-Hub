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

可以在描述中适当举例，若参数是地点，可以举例“比如说北京，上海”


{
  "id": "d63a379f-1a18-4eae-b32e-af280f2aa249",
  "choices": [
    {
      "finish_reason": "stop",
      "index": 0,
      "logprobs": null,
      "message": {
        "content": "你好！我是你的助手，有什么可以帮你的吗？",
        "refusal": null,
        "role": "assistant",
        "annotations": null,
        "audio": null,
        "function_call": null,
        "tool_calls": null
      }
    }
  ],
  "created": 1790061174,
  "model": "deepseek-flash",
  "object": "chat.completion",
  "metadata": null,
  "moderation": null,
  "service_tier": null,
  "system_fingerprint": "aeb56401ca74e127821c4f9126dcb669",
  "usage": {
    "completion_tokens": 12,
    "prompt_tokens": 621,
    "total_tokens": 633,
    "completion_tokens_details": null,
    "prompt_tokens_details": {
      "audio_tokens": null,
      "cache_write_tokens": null,
      "cached_tokens": 0,
      "image_tokens": null,
      "text_tokens": null
    },
    "prompt_cache_hit_tokens": 0,
    "prompt_cache_miss_tokens": 621
  }
}

用 tool_calls/content 驱动主流程，用 finish_reason 解释结束状态。


```