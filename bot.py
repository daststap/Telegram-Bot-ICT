import telebot
from telebot import types
import sqlite3
import csv
import pandas
from telebot.types import ReplyKeyboardRemove
import openpyxl
import random

token = "7675952692:AAHKjdcepZ96YBK_asQ6_IT8I2h6kWCLlkA"
bot = telebot.TeleBot(token)

page = 'start'

main_keyboard = [types.KeyboardButton("Теория"), types.KeyboardButton("Практика")]
practical_keyboard = [types.KeyboardButton("Решить задачу"), types.KeyboardButton("Где я ошибался"),
                      types.KeyboardButton("Пройти тестирование по некоторым задачам"), types.KeyboardButton("Назад")]
theory_keyboard = [types.KeyboardButton("Посмотреть термины"), types.KeyboardButton("Просмотреть теорию"), types.KeyboardButton("Назад")]
show_terms_keyboard = [types.KeyboardButton("Посмотреть опрелелённый термин"), types.KeyboardButton("Посмотреть все термины"), types.KeyboardButton("Назад")]
do_task_keyboard = [types.KeyboardButton("Решить случайную задачу"), types.KeyboardButton("Назад")]


def get_data_from_table(filename):
    lst = []
    with open(filename) as table:
        table_data = csv.reader(table, delimiter=',')
        next(table_data)
        for row in table_data:
            lst.append(row)
        return lst


def get_current_poll(index, filename):
    data_list = get_data_from_table(filename)
    current_poll = data_list[index]
    return current_poll


def open_terms():
    res = pandas.read_csv('terms.csv')
    return res


def open_puz(index):
    res = pandas.read_csv('test_with_picture.csv')
    list_questions = list(res['question'])
    list_ans1 = list(res['answer1'])
    list_ans2 = list(res['answer2'])
    list_ans3 = list(res['answer3'])
    list_ans4 = list(res['correct_option_id'])
    list_exp = list(res['explanation'])
    list_extra = list(res['extra_files'])
    return list_questions[index], list_ans1[index], list_ans2[index], list_ans3[index], list_ans4[index], list_exp[
        index], list_extra[index]


@bot.message_handler(commands=['start'])
def start_message(message):
    markup = types.ReplyKeyboardMarkup()
    for i in main_keyboard:
        markup.add(i)
    bot.send_message(message.chat.id, f"Здравствуйте, {message.from_user.first_name}", reply_markup=markup)
    bot.send_message(message.chat.id, f"Это Телеграм Бот с помощью которого вы сможете изучить материалы и типы "
                                      f"заданий для подготовки к ЕГЭ по информатике", reply_markup=markup)
    bot.send_message(message.chat.id,
                     f"А также вы можете проходить тестирования для закрепления выученного материала.",
                     reply_markup=markup)
    bot.send_message(message.chat.id, '[Источник данных](https://inf-ege.sdamgia.ru/)', parse_mode='Markdown')
    connection = sqlite3.connect('user_data.db', check_same_thread=False)
    cursor = connection.cursor()
    username = message.from_user.username
    cursor.execute('DELETE FROM with_cor_ans WHERE username = ?', (username,))
    connection.commit()
    connection.close()


@bot.poll_answer_handler()
def handle_poll_answers(poll_answer):
    connection = sqlite3.connect('user_data.db', check_same_thread=False)
    cursor = connection.cursor()
    answer_user = poll_answer.option_ids[0]
    username = poll_answer.user.id
    num_puz = poll_answer.poll_id
    cursor.execute('INSERT INTO only_answers (username, question_id, answer) VALUES (?, ?, ?)',
                   (f"{str(username)}", f"{str(num_puz)}", f"{str(answer_user)}"))
    connection.commit()
    connection.close()


@bot.message_handler(content_types=['text'])
def message_reply(message):
    comp_text = False
    try:
        l = message.text.split()
        flag = False
        for i in l:
            if not i.isdigit():
                flag = True
        if not flag:
            comp_text = True
    except:
        pass
    text = message.text
    connection = sqlite3.connect('user_data.db', check_same_thread=False)
    cursor = connection.cursor()
    if text == "Теория":
        markup = types.ReplyKeyboardMarkup()
        for i in theory_keyboard:
            markup.add(i)
        bot.send_message(message.chat.id, 'Теоретический раздел', reply_markup=markup)
    elif text == "Практика":
        markup = types.ReplyKeyboardMarkup()
        for i in practical_keyboard:
            markup.add(i)
        bot.send_message(message.chat.id, 'Практический раздел', reply_markup=markup)
    elif text == "Где я ошибался":
        page = 'user_info'
        usn = str(message.from_user.id)
        cursor.execute("SELECT request, is_correct FROM with_cor_ans WHERE username = ?", (usn,))
        data = cursor.fetchall()
        mistakes = []
        for i in data:
            if list(i)[-1] == '0':
                mistakes.append(list(i)[0])
        if len(mistakes) == 0:
            bot.send_message(message.chat.id, text="Вы ещё не допускали ошибок")
        else:
            bot.send_message(message.chat.id, text=f"История ошибок пользователя")
            markup = types.InlineKeyboardMarkup(row_width=1)
            for i in range(len(mistakes)):
                t = types.InlineKeyboardButton(text=f'{mistakes[i]}', callback_data=f'problem{mistakes[i]}')
                markup.add(t)
            bot.send_message(message.chat.id, 'Выберите задачу', reply_markup=markup)
    elif text == "Просмотреть теорию":
        markup = types.InlineKeyboardMarkup(row_width=1)
        lst = pandas.read_csv("topics_table.csv")
        for i in range(len(lst)):
            t = types.InlineKeyboardButton(text=f'{i + 1} {lst.iloc[i][0]}', callback_data=f'topic{i + 1}')
            markup.add(t)
        bot.send_message(message.chat.id, 'Выберите тему:', reply_markup=markup)
    elif text == "Решить задачу":
        page = 'testing'
        markup = types.ReplyKeyboardMarkup()
        for i in do_task_keyboard:
            markup.add(i)
        bot.send_message(message.chat.id, text="Введите, пожалуйста, номер задачи или решите случайную задачу",
                         reply_markup=markup)
    elif text == "Решить случайную задачу":
        page = 'random_puzzle'
        index = random.randint(1, 9)
        qu, ans1, ans2, ans3, cor_ans, exp, num_of_extra = open_puz(index - 1)
        photo = open(f'puzzles\\{index}_usl.png', 'rb')
        bot.send_photo(message.chat.id, photo)
        try:
            extra = open(f'additional\\{index}.xlsx', 'rb')
            bot.send_document(message.chat.id, extra)
            extra.close()
        except:
            pass
        markup = types.ReplyKeyboardMarkup()
        solution = types.KeyboardButton("Просмотреть решение задачи " + f"{index}")
        sol_1 = types.KeyboardButton("Назад")
        markup.add(solution)
        markup.add(sol_1)
        bot.send_poll(message.chat.id, question="Ваш вариант ответа", options=[str(ans1), str(ans2), str(ans3)],
                        allows_multiple_answers=False, is_anonymous=False, type="quiz",
                        correct_option_id=int(cor_ans) - 1,
                        explanation=exp, reply_markup=markup)
        cursor.execute('INSERT INTO Polls (username, msg_id) VALUES (?, ?)',
                           (f"{str(message.from_user.id)}", f"{str(message.message_id + 2)}"))
        connection.commit()
        cursor.execute('INSERT INTO only_cor_answers_puz (num_puz, username, cor_ans) VALUES (?, ?, ?)',
                        (f"{str(index)}", f"{str(message.from_user.id)}", f"{str(int(cor_ans) - 1)}"))
        connection.commit()
    elif text[:19] == "Просмотреть решение":
        usn = str(message.from_user.id)
        cursor.execute("SELECT msg_id FROM Polls WHERE username = ?", (usn,))
        data11 = cursor.fetchall()
        page = 'show_answer'
        index = int(text[26:])
        photo = open(f'puzzles\\{index}_resh.png', 'rb')
        bot.send_photo(message.chat.id, photo, reply_markup=ReplyKeyboardRemove())
        markup = types.ReplyKeyboardMarkup()

        for i in main_keyboard:
            markup.add(i)
        cursor.execute("SELECT answer FROM only_answers WHERE username = ?", (usn,))
        data1 = cursor.fetchall()
        cursor.execute("SELECT cor_ans FROM only_cor_answers_puz WHERE username = ?", (usn,))
        data2 = cursor.fetchall()
        cursor.execute("SELECT num_puz FROM only_cor_answers_puz WHERE username = ?", (usn,))
        data3 = cursor.fetchall()
        num_puz = list(data3[-1])[0]
        is_correct = 0
        if list(data1[-1])[0] == list(data2[-1])[0]:
            is_correct = 1

        cursor.execute('INSERT INTO with_cor_ans (username, request, answer, is_correct) VALUES (?, ?, ?, ?)',
                       (f"{str(message.from_user.id)}", f"{str(num_puz)}", f"{str(list(data1[-1])[0])}",
                        f"{str(is_correct)}"))
        connection.commit()
        bot.send_message(message.chat.id, f"Надеемся, у Вас получилось разобраться с решением, можете ввести "
                                          f"номер задачи для продолжения или перейти в другой режим работы бота",
                         reply_markup=markup)

    elif text.isdigit():
        page = 'input_num_of_puzzle'
        index = int(text)
        if not 1 <= index <= 9:
            bot.send_message(message.chat.id, "Такого номера не существует, плак(")
        else:
            qu, ans1, ans2, ans3, cor_ans, exp, num_of_extra = open_puz(index - 1)
            photo = open(f'puzzles\\{index}_usl.png', 'rb')
            bot.send_photo(message.chat.id, photo)
            try:
                extra = open(f'additional\\{index}.xlsx', 'rb')
                bot.send_document(message.chat.id, extra)
                extra.close()
            except:
                pass
            markup = types.ReplyKeyboardMarkup()
            solution = types.KeyboardButton("Просмотреть решение задачи " + f"{index}")
            sol_1 = types.KeyboardButton("Назад")
            markup.add(solution)
            markup.add(sol_1)
            bot.send_poll(message.chat.id, question="Ваш вариант ответа", options=[str(ans1), str(ans2), str(ans3)],
                          allows_multiple_answers=False, is_anonymous=False, type="quiz",
                          correct_option_id=int(cor_ans) - 1,
                          explanation=exp, reply_markup=markup
                          )
            cursor.execute('INSERT INTO Polls (username, msg_id) VALUES (?, ?)',
                           (f"{str(message.from_user.id)}", f"{str(message.message_id + 2)}"))
            connection.commit()
            cursor.execute('INSERT INTO only_cor_answers_puz (num_puz, username, cor_ans) VALUES (?, ?, ?)',
                           (f"{str(text)}", f"{str(message.from_user.id)}", f"{str(int(cor_ans) - 1)}"))
            connection.commit()
    elif text == "Посмотреть термины":
        page = 'show_terms'
        markup = types.ReplyKeyboardMarkup()
        for i in show_terms_keyboard:
            markup.add(i)
        bot.send_message(message.chat.id, "Выберите режим работы просмотра терминов", reply_markup=markup)
    elif text == "Посмотреть опрелелённый термин":
        page = 'opr_term'
        markup = types.ReplyKeyboardMarkup()
        for i in main_keyboard:
            markup.add(i)
        bot.send_message(message.chat.id, "Введите термин:", reply_markup=markup)
    elif text == "Посмотреть все термины":
        markup = types.ReplyKeyboardMarkup()
        for i in main_keyboard:
            markup.add(i)
        bot.send_message(message.chat.id, '[Таблица терминов](https://telegra.ph/Tablica-Terminov-Po-Infomatike-05-02)',
                         parse_mode='Markdown')
    elif text == "Пройти тестирование по некоторым задачам":
        page = 'pers_test'
        bot.send_message(message.chat.id, text="Введите, пожалуйста номера задач, из которых будет состоять Ваше "
                                               "персональное тестирование, используйте в качестве разделителя "
                                               "пробел")
    elif comp_text:
        markup = types.InlineKeyboardMarkup(row_width=1)
        for i in range(len(l)):
            t = types.InlineKeyboardButton(text=f'{l[i]}', callback_data=f'problem{l[i]}')
            markup.add(t)
        bot.send_message(message.chat.id, 'Задачи для Вашего тестирования', reply_markup=markup)
    elif text == "Назад":
        keyboard = types.ReplyKeyboardMarkup()
        for i in main_keyboard:
            keyboard.add(i)
        bot.send_message(chat_id=message.chat.id, text="Выбрано главное меню", reply_markup=keyboard)
    else:
        page = "term_input"
        markup = types.ReplyKeyboardMarkup()
        for i in main_keyboard:
            markup.add(i)
        cursor.execute("SELECT term, opr FROM Terms")
        data1 = cursor.fetchall()
        flag = False
        for i in data1:
            term = list(i)[0]
            opr = list(i)[1]
            if text.lower() in term.lower():
                bot.send_message(message.chat.id, f"{term} - {opr}", reply_markup=markup)
                flag = True
        if not flag:
            bot.send_message(message.chat.id, f"К сожалению, мы не нашли этот термин, проверьте, пожалуйста, правильность ввода", reply_markup=markup)


@bot.callback_query_handler(func=lambda callback: callback.data)
def check_keyboard_data(callback):
    topics_list = pandas.read_csv("topics_table.csv")
    razbori = pandas.read_csv("razbori.csv")
    if callback.data == "Назад":
        markup = types.InlineKeyboardMarkup(row_width=1)
        lst = pandas.read_csv("topics_table.csv")
        for i in range(len(lst)):
            t = types.InlineKeyboardButton(text=f'{i + 1} {lst.iloc[i][0]}', callback_data=f'topic{i + 1}')
            markup.add(t)
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.id, text='Выберите тему:',
                              reply_markup=markup)
    if callback.data[:5] == "topic":
        index = int(callback.data[5:]) - 1
        markup = types.InlineKeyboardMarkup(row_width=1)
        l = topics_list.iloc[index]
        l = l.dropna()
        for i in range(1, len(l)):
            t = types.InlineKeyboardButton(text=f'{l[i]}', callback_data=f'{i + 1}subtopic{index + 1}')
            markup.add(t)
        back = types.InlineKeyboardButton(text="Назад", callback_data="Назад")
        markup.add(back)
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.id,
                              text='Выберите подтему:', reply_markup=markup)
        x = razbori.iloc[index]
        bot.send_message(chat_id=callback.message.chat.id,
                         text=x, reply_markup=None)
    elif callback.data[1:9] == "subtopic":
        i = int(callback.data[0])
        index = int(callback.data[9:]) - 1

        l = topics_list.iloc[index]
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.id,
                              text=f"{l.iloc[i-1]}", reply_markup=None)

        file = open(f"theory\\{i - 1}theory{index + 1}.pdf", 'rb')
        bot.send_document(chat_id=callback.message.chat.id, document=file, caption="Задачи")
    elif callback.data[:7] == "problem":
        text = callback.message.text
        connection = sqlite3.connect('user_data.db', check_same_thread=False)
        cursor = connection.cursor()
        index = int(callback.data[7:])
        if not 1 <= index <= 9:
            bot.send_message(chat_id=callback.message.chat.id,
                             text=f"Такого номера не существует, плак(", reply_markup=None)
        else:
            bot.send_message(chat_id=callback.message.chat.id,
                             text=f"Задача номер {index}", reply_markup=None)
            qu, ans1, ans2, ans3, cor_ans, exp, num_of_extra = open_puz(index - 1)
            photo = open(f'puzzles\\{index}_usl.png', 'rb')
            bot.send_photo(callback.message.chat.id, photo)
            try:
                extra = open(f'additional\\{index}.xlsx', 'rb')
                bot.send_document(callback.message.chat.id, extra)
                extra.close()
            except:
                pass
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            solution = types.KeyboardButton("Просмотреть решение задачи " + f"{index}")
            sol_1 = types.KeyboardButton("Назад")
            markup.add(solution)
            markup.add(sol_1)
            bot.send_poll(callback.message.chat.id, question="Ваш вариант ответа",
                          options=[str(ans1), str(ans2), str(ans3)],
                          allows_multiple_answers=False, is_anonymous=False, type="quiz",
                          correct_option_id=int(cor_ans) - 1,
                          explanation=exp, reply_markup=markup
                          )
            cursor.execute('INSERT INTO Polls (username, msg_id) VALUES (?, ?)',
                           (f"{str(callback.message.chat.id)}", f"{str(callback.message.message_id + 2)}"))
            connection.commit()
            cursor.execute('INSERT INTO only_cor_answers_puz (num_puz, username, cor_ans) VALUES (?, ?, ?)',
                           (f"{str(index)}", f"{str(callback.message.chat.id)}", f"{str(int(cor_ans) - 1)}"))
            connection.commit()


bot.polling(none_stop=True)

