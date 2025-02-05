from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import pprint



class HuggingfaceChatbot:
    def __init__(self, model, max_mem_per_gpu='80GiB'):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = self.load_hugging_face_model(model, max_mem_per_gpu)
        self.tokenizer = AutoTokenizer.from_pretrained(model)
        


    def load_hugging_face_model(self, model, max_mem_per_gpu='80GiB'):
        MAX_MEM_PER_GPU = max_mem_per_gpu
        map_list = {}
        for i in range(torch.cuda.device_count()):
            map_list[i] = MAX_MEM_PER_GPU
        model = AutoModelForCausalLM.from_pretrained(
            model,
            #device_map="auto",
            #max_memory=map_list,
            #torch_dtype="auto",
            #cache_dir = "./",
            #trust_remote_code=True
        ).to(self.device)
        return model

    def respond(self, message, max_new_tokens=128):
        message = message.replace("Assistant:", "").strip()
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": message}
        ]
        message = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        input_ids = self.tokenizer(message).input_ids
        input_ids = torch.tensor(input_ids).view(1,-1).to(self.model.device)
        generation_config = self.model.generation_config
        generation_config.max_length = 8192
        generation_config.max_new_tokens = max_new_tokens
        output = self.model.generate(
            input_ids,
            generation_config=generation_config
        )
        response = self.tokenizer.batch_decode(output[:, input_ids.shape[1]:], skip_special_tokens=True)[0]
        response = response.strip()
        return response

if __name__ == '__main__':
    model = AutoModelForCausalLM.from_pretrained(
        "meta-llama/Meta-Llama-3-8B-Instruct",
    ).to("cuda:0")
    tokenizer = AutoTokenizer.from_pretrained("meta-llama/Meta-Llama-3-8B-Instruct")
    print(1)