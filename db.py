from bs4 import BeautifulSoup
import colorama
from colorama import Fore
import requests
import csv


class Task:

    def __init__(self, text, images=None, table=None, file=None, answer="", task_id=0):
        self.text = text
        self.images = set()
        self.table = table
        self.answer = answer
        self.file = set()
        self.task_id = task_id
        self.solutionLink = False

    def __eq__(self, other):
        return (self.text, self.images, self.table, self.answer, self.task_id) == (
            other.text, other.images, other.table, other.answer, other.task_id)

    def __str__(self):
        return "id: {}, {}".format(self.task_id, self.text)


class Solver:
    def __init__(self, variant_link, cookies):
        self.url_variant = variant_link
        self.url_domain = variant_link[:variant_link.index("/", 10) + 1]
        self.url_search = self.url_domain + "search?search={}&cb=1&body=3&text=2&page="
        self.url_task = self.url_domain + "problem?id="

        self.cookies = cookies

    def get_tasks(self, url):
        response = requests.get(url, cookies=self.cookies)
        soup = BeautifulSoup(response.text, "lxml")

        tasks = []
        for taskHTML in soup.findAll("div", class_="prob_maindiv"):
            task = None

            for p in taskHTML.findAll("p"):
                if p.text and p.text.strip() and not p.text.strip()[0].isdigit():
                    task = Task(p.text.replace("­", ""))
                    break

            for img in taskHTML.findAll("img"):
                src = img["src"]
                if not src.startswith("http"):
                    src = self.url_domain[:-1] + src
                task.images.add(src)

            for a in taskHTML.findAll("a", href=True):
                if a.text and a.text.endswith(".xlsx"):
                    task.file.add(self.url_domain + a["href"])

            answers = taskHTML.findAll("div", class_="answer")
            if answers:
                task.answer = answers[-1].text.rstrip(".").replace("Ответ: ", "").replace("&", " ")

            link = taskHTML.find("a", href=True)
            if link:
                task.task_id = link.text

            same_text = taskHTML.find("div", class_="probtext")
            if same_text and same_text.has_attr("id"):
                task.task_id = same_text["id"][4:]

            table = taskHTML.find("table")
            arr = []
            if table:
                rows = table.find_all("tr")
                for row in rows:
                    cols = row.find_all("td")
                    cols = [col.text for col in cols]
                    arr.append(cols)
                task.table = arr
                arr = []



            if "Впишите ответ на задание в поле выше или загрузите его" in taskHTML.parent.parent.text or \
                    "Решения заданий с развернутым ответом" in taskHTML.parent.parent.text:
                task.solutionLink = True

            tasks.append(task)
        return tasks

    def get_answer(self, task):
        if not task.answer and task.task_id:
            if task.solutionLink:
                task.answer = self.url_task + str(task.task_id)
            else:
                task.answer = self.get_tasks(self.url_task + task.task_id)[0].answer
        else:
            query = task.text
            if len(query) >= 200:
                query = query[:200].rsplit(" ", 1)[0]
            search_url = self.url_search.format(query.replace(" ", "%20"))

            search_page = 0
            prev_search_results = ""
            while task.answer == "":
                search_page += 1
                search_results = self.get_tasks(search_url + str(search_page))
                if search_results == prev_search_results:
                    break

                for result in search_results:
                    if task.text == result.text and task.images & result.images == task.images:
                        task.task_id = result.task_id
                        if task.solutionLink:
                            task.answer = self.url_task + str(task.task_id)
                        else:
                            task.answer = result.answer
                        break
                prev_search_results = search_results
        if not task.answer:
            task.answer = "Не найдено"

def save_to_csv(task, filename):
    fieldnames = ["text", "img", "table", "file", "answer"]
    with open(filename, "a", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerow({"text": task.text})
        writer.writerow({"img": task.images})
        writer.writerow({"table": task.table})
        writer.writerow({"file": task.file})
        writer.writerow({"answer": task.answer})

def main():
    colorama.init()
    cookies = {}
    task_start = 15492934
    task_end = 15599999
    for i in range(task_start, task_end + 1):
         solver = Solver(f"https://inf-ege.sdamgia.ru/test?id={i}", cookies)

    task_num = 0
    for i in range(task_start, task_end + 1):
        for task in solver.get_tasks(f"https://inf-ege.sdamgia.ru/test?id={i}"):
            task_num += 1
        if not task.answer:
            solver.get_answer(task)
        save_to_csv(task, "task.csv")
    print("Готово")
    input()

if __name__ == '__main__':
    main()