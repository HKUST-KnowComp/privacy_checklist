import re

class LlamaParser:
    def __init__(self):
        self.section_pattern = r"[0-9]+\.[0-9]+(\([0-9A-Za-zivx]+\))*"
        self.law_generation_errors = []
        self.law_judge_errors = []
        self.decision_errors = []
    def parse_conclusion(self, response):
        return response.split("\n")[-1]

    def parse_law(self, response):

        if "Generated Related HIPAA Regulations:".lower() not  in response.lower():
            raise ValueError("Law Value Error")
        else:
            gen_idx = response.lower().index("Generated Related HIPAA Regulations:".lower())
            response = response[gen_idx:]


        ret = []
        response = response.split("\n")
        for r in response:
            search = re.search(self.section_pattern, r)
            if search is None:
                continue
            start, end = search.span()
            item_number = r[start:end]
            # content = r[end:]

            ret.append(item_number)

        # if not ret:
        #     self.law_generation_errors.append("\n".join(response))
        #     raise ValueError("Did not generate regulations!\n")
        return ret

    def parse_law_beam(self, response):
        ret_lookup, ret_selected = [],[]
        if not "lookup:" in response.lower() or not "selected:" in response.lower() :
            raise ValueError("Beam Value Error!")

        idx = response.lower().index("selected:")
        lookup = response[:idx]
        selected = response[idx:]
        for item in lookup.split("\n"):
            search = re.search(self.section_pattern, item)
            if search is None: continue
            if " - " not in item: continue
            start, end = search.span()
            item_number = item[start:end]
            ret_lookup.append(item_number)

        for item in selected.split("\n"):
            search = re.search(self.section_pattern, item)
            if search is None: continue
            if " - " not in item: continue
            start, end = search.span()
            item_number = item[start:end]
            ret_selected.append(item_number)
        return ret_lookup, ret_selected

    def parse_law_filter(self, response):
        ret = {}
        ret["response"] = response
        filtered = []
        if "Selected Related HIPAA Regulations:".lower() not in response.lower():
            raise ValueError("Filter Value Error!")
        idx = response.lower().index("Selected Related HIPAA Regulations:".lower())
        response = response[idx:]
        response = response.split("\n")
        for r in response:
            search = re.search(self.section_pattern, r)
            if search is None:
                continue
            if " - " not in r: continue
            start, end = search.span()
            item_number = r[start:end]
            filtered.append(item_number)
        ret["filtered"] = filtered
        return ret


    def parse_law_judge(self, response):
        ret = {}
        response = response.split("\n")
        for r in response:
            if "judgment:" in r.lower():
                if "no" in r.lower():
                    ret["decision"] = "no"
                elif "yes" in r.lower():
                    ret["decision"] = "yes"

            if "reason:" in r.lower():
                # splited_r = " ".join(r.split(".")[1:]).strip()
                ret["reason"] = r

        # if not "decision" in ret or not "reason" in ret:
        if not "decision" in ret:
            self.law_judge_errors.append("\n".join(response))
            raise ValueError("Law Judge Value Error!")
        return ret

    def parse_law_content(self, response):
        response = response.replace("*", ":")
        if "HIPAA Privacy Rule:".lower() not in response.lower() or "references:" not in response.lower():
            raise ValueError("HIPAA Content Error!")
        idx = response.lower().index("HIPAA Privacy Rule:".lower())
        response = response[idx:]
        idx = response.lower().index("references:")
        response = response[:idx]
        response = response.split("\n")
        response = " ".join(response).strip().replace(":","").replace("\n"," ")
        # cr = []
        # for r in response.split("\n"):
        #     if "HIPAA Privacy Rule:" in r or "HIPAA Security Rule:" in r or "Minimum Necessary Standard:" in r:
        #         cr.append(r)
        # if not cr:
        #     raise ValueError("HIPAA Content Error!")
        # response = " ".join(cr).strip().replace(":", "")
        return response


    def parse_decision(self, response):
        ret = {"response":response}
        response = response.split("\n")
        for r in response:
            if "choice:" in r.lower():
                if "not related" in r.lower():
                    ret["decision"] = "not applicable"
                elif "permitted" in r.lower():
                    ret["decision"] = "positive"
                elif "prohibited" in r.lower():
                    ret["decision"] = "negative"
            if "reason:" in r.lower():
                ret["reason"] = r

        if not "decision" in ret:
            self.decision_errors.append("\n".join(response))
            raise ValueError("Decision Value Error!")
        return ret


    def parse_decision_judge(self, response):
        ret = {}
        response = response.split("\n")
        for r in response:
            if "judgment:" in r.lower():
                if "no" in r.lower():
                    ret["decision"] = "no"
                elif "yes" in r.lower():
                    ret["decision"] = "yes"

            if "reason:" in r.lower():
                ret["reason"] = r

        if not "decision" in ret or not "reason" in ret:
            raise ValueError("Law Judge Value Error!")
        return ret

    def parse_cot_auto(self, response):
        ret = {"response":response}
        response = response.split("\n")
        for r in response:
            if "choice:" in r.lower():
                if "not related" in r.lower() or "irrelated" in r.lower() or "not relevant" in r.lower() or "irrelevant" in r.lower():
                    ret["decision"] = "not applicable"
                elif "permitted" in r.lower():
                    ret["decision"] = "positive"
                elif "prohibited" in r.lower():
                    ret["decision"] = "negative"
            if "reason:" in r.lower():
                ret["reason"] = r

        if not "decision" in ret:
            self.decision_errors.append("\n".join(response))

            raise ValueError("Decision Value Error!")
        return ret
    
    def parse_yes_no(self, response):
        ret = {}
        ret["response"] = response
        response = response.split("\n")
        for r in response:
            if "yes" in r.lower():
                ret["decision"] = "yes"
            elif "no" in r.lower():
                ret["decision"] = "no"
            break
        if not "decision" in ret:
            self.decision_errors.append("\n".join(response))
            raise ValueError("Law Judge Value Error!")
        return ret

class ChatgptParser:
    def __init__(self):
        self.section_pattern = "§[0-9]+\.[0-9]+(\([0-9A-Za-zivx]+\))*"
        self.content_pattern  = "§[0-9]+\.[0-9]+(\([0-9A-Za-zivx]+\))*.*?(?=§|$|[A-Z])"

    def match_HIPAA_section(self, string):
        all_sections = re.search(self.section_pattern, string)
        return all_sections
    def parse_references(self, string):
        pattern = "Reference(s):"
        if pattern not in string:
            return -1
        return string.index(pattern)

    def parse_answer(self, string):
        find = re.search("HIPAA Violation:", string)
        if find is None:
            return "error"
        end = find.end()
        sub_string = string[end:].lower().strip()
        if sub_string.startswith("no"):
            return "negative"
        elif sub_string.startswith("yes"):
            return "positive"
        else:
            return "error"


    def match_reference_content(self, string):
        all_contents = re.search(self.content_pattern, string, re.DOTALL)
        return all_contents

    def collect_section(self,string):
        sections = []
        while True:
            find = self.match_HIPAA_section(string)
            if find is None:
                return sections
            start, end = find.span()
            sections.append(string[start:end])
            string = string[end:]

    def collect_content(self,string):
        contents = []
        while True:
            find = self.match_reference_content(string)
            if find is None:
                return contents
            start, end = find.span()
            contents.append(string[start:end])
            string = string[end:]



if __name__ == '__main__':
    print(0)