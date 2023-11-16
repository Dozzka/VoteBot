import telebot
from peewee import *
import time
from telebot import types


bot = telebot.TeleBot('6390668045:AAFym5Et1ZJ38Pvm3ugxAPvpkejB1pdkivI')

# Создаем базу данных  для хранения пользователей
db = SqliteDatabase('Data.db')


class User(Model):
    id = PrimaryKeyField()
    nickname = CharField(max_length=255)

    class Meta:
        database = db


class Votes(Model):
    user_id = PrimaryKeyField()
    name_of_project = CharField(max_length=255)
    mark = FloatField()


    class Meta:
        database = db


class Result(Model):
    Result_id = PrimaryKeyField()
    flag = BooleanField()
    Name = CharField(max_length=255)
    Average_mark = FloatField()

    class Meta:
        database = db


db.connect()
db.create_tables([User])
db.create_tables([Votes])
db.create_tables([Result])


YOUR_USER_ID = 899338185
TimeGolos = 30


@bot.message_handler(commands=['start'])
def handle_start(message):

    user_id = message.from_user.id
    username = message.from_user.first_name
    existing_user = User.get_or_none(User.id == user_id)


    if existing_user:
        bot.send_message(user_id, 'Вы уже добавлены в базу данных')

    else:
        User.create(id=user_id, nickname=username)
        bot.send_message(user_id, 'Вы были добавлены в базу данных.')


@bot.message_handler(commands=['time'])
def handle_vote(message):
    if message.from_user.id == YOUR_USER_ID:
        bot.send_message(message.chat.id, 'Введите время в секундах:')
        bot.register_next_step_handler(message,changer_time)

    else:
        bot.send_message(message.chat.id, 'У вас нет разрешения на изменения времени голосования.')

def changer_time(message):
    global TimeGolos
    try:
        new_time = int(message.text)
        TimeGolos = new_time
        bot.send_message(message.chat.id, f'Время изменено на {new_time} секунд.')
    except:
        bot.send_message(message.chat.id, 'Пожалуйста, введите корректное число секунд для времени.')
        bot.register_next_step_handler(message,changer_time)




@bot.message_handler(commands=['vote'])
def handle_vote(message):
    if message.from_user.id == YOUR_USER_ID:
        bot.send_message(message.chat.id, 'Введите имя проекта для голосования:')
        bot.register_next_step_handler(message, start_voting)

    else:
        bot.send_message(message.chat.id, 'У вас нет разрешения на голосование.')


def start_voting(message):

    project_name = message.text
    Result.create(flag=True, Name=project_name,Average_mark = 0)


    # Создаем клавиатуру с оценками
    KeyForVote = types.InlineKeyboardMarkup()
    bt1 = types.InlineKeyboardButton(text=str(1), callback_data=f'vote_{1}_{project_name}')
    bt2 = types.InlineKeyboardButton(text=str(2), callback_data=f'vote_{2}_{project_name}')
    bt3 = types.InlineKeyboardButton(text=str(3), callback_data=f'vote_{3}_{project_name}')

    bt4 = types.InlineKeyboardButton(text=str(4), callback_data=f'vote_{4}_{project_name}')
    bt5 = types.InlineKeyboardButton(text=str(5), callback_data=f'vote_{5}_{project_name}')
    KeyForVote.add(bt1, bt2, bt3, row_width=3)
    KeyForVote.add(bt4, bt5, row_width=2)

    # Рассылка
    user_ids = [user.id for user in User.select(User.id)]


    for user_id in user_ids:
        bot.send_message(user_id,
                         f'Голосование начато для проекта "{project_name}".\nПоставьте оценку от 1 до 5, нажав на соответствующую кнопку:',
                         reply_markup=KeyForVote)

    # Запускаем таймер на N секунд для окончания голосования

    time.sleep(TimeGolos)
    show_voting_results()
    db.close()

@bot.callback_query_handler(func=lambda call: call.data.startswith('vote_'))
def handle_vote_callback(call):

    data = call.data.split('_')
    vote = int(data[1])
    project_name = data[2]
    user_id = call.from_user.id


    current_proj = Result.select(Result.Name).where(Result.flag == True).scalar()


    if current_proj == project_name:
        # Проверяем, голосовал ли пользователь ранее, и обновляем его голос
        existing_vote = Votes.select().where(Votes.user_id == user_id).first()

        if existing_vote:
            existing_vote.name_of_project = current_proj
            existing_vote.mark = vote
            existing_vote.save()
        else:
            Votes.create(user_id=user_id, mark=vote, name_of_project=project_name)

        bot.answer_callback_query(call.id, f'Вы поставили оценку {vote} проекту "{project_name}".')

    else:
        bot.answer_callback_query(call.id, 'Голосование закончилось')


def show_voting_results():

    current_proj = Result.select(Result.Name).where(Result.flag == True).scalar()

    voting_results = [Votes.mark for Votes in Votes.select().where(Votes.name_of_project == current_proj)]



    if len(voting_results) != 0:

        Result.update(flag = False, Average_mark = round(sum(voting_results) / len(voting_results),2)).where(Result.Name == current_proj).execute()

        user_ids = [user.id for user in User.select(User.id)]

        for user_id in user_ids:
            bot.send_message(user_id,
                             f'Голосование окончено за "{current_proj}".\nСредняя оценка: {round(sum(voting_results) / len(voting_results),2)}')

    else:
        user_ids = [user.id for user in User.select(User.id)]
        Result.update(flag=False, Average_mark=0.0).where(Result.Name == current_proj).execute()
        for user_id in user_ids:
            bot.send_message(user_id,
                             f'Голосование закончено "{current_proj}".\nНикто не проголосовал (')

    voting_results.clear()




if __name__ == '__main__':
    bot.polling(none_stop=True)
