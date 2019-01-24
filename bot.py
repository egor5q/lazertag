# -*- coding: utf-8 -*-
import os
import telebot
import time
import random
import threading
from emoji import emojize
from telebot import types
from pymongo import MongoClient


token = os.environ['TELEGRAM_TOKEN']
bot = telebot.TeleBot(token)


client=MongoClient(os.environ['database'])
db=client.lazertag
users=db.users

games=[]

@bot.message_handler(commands=['help'])
def help(m):
    bot.send_message(m.chat.id, 'Информация на данный момент отсутствует, напишите @Loshadkin.')

@bot.message_handler(commands=['start'])
def start(m):
   x=users.find_one({'id':m.from_user.id})
   if x==None:
      users.insert_one(createuser(m.from_user.id,m.from_user.first_name,m.from_user.username))
      bot.send_message(m.chat.id, m.from_user.first_name+', приветствую в игре "Лазертаг"! Цель этой игры - остаться единственной '+
                       'живой командой в игре! Подробности по команде /help.')
        
@bot.message_handler(commands=['preparegame'])
def preparegame(m):
    no=0
    for ids in games:
        if games[ids]['id']==m.chat.id:
            no=1
    if no==0:
        kb=types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(text='Сменить команду', callback_data='teamchoice'))
        msg=bot.send_message(m.chat.id, 'Начинаем сбор игроков! Жмите /tagjoin для вступления в игру.',reply_markup=kb)
        games.append(creategame(m.chat.id,msg))
        

@bot.message_handler(commands=['tagjoin'])
def tagjoin(m):
    yes=0
    for ids in games:
        if ids['id']==m.chat.id:
            yes=1
            game=ids
    if yes==1:
        game['teams'].append(createteam(game)) 
        x=createplayer(m.from_user.id)
        if x!=None:
            try:
                bot.send_message(m.from_user.id, 'Вы успешно присоединились!')
                game['teams'][len(game['teams'])-1]['players'].append(x)
                medit(editmessage(game['message'],game),game['message'].chat.id,game['message'].message_id)
            except:
                bot.send_message(m.chat.id, 'Сначала напишите /start боту @Lazertagbot в личку!')
        else:
            bot.send_message(m.chat.id, 'Сначала напишите /start боту @Lazertagbot в личку!')
        
        
        
def medit(message_text,chat_id, message_id,reply_markup=None,parse_mode=None):
    return bot.edit_message_text(chat_id=chat_id,message_id=message_id,text=message_text,reply_markup=reply_markup,
                                 parse_mode=parse_mode)  


def editmessage(msg,game):
    text=''
    for ids in game['teams']:
        t=ids
        text+='Команда '+t['name']+':\n'
        for idss in t['players']:
            player=idss
            if idss!=len(t['players'])-1:
                symbol='┞'
            else:
                symbol='┕'
            text+=symbol+player['name']+'\n'
        text+='\n'
    return text
        

def randomgen(teams):
    allids=[]
    for ids in teams:
        allids.append(ids['id'])
    i=0
    x=''
    while i<3:
        i=random.randint(0,9)
        x+=str(i)
        i+=1
    while x in allids:
        x=''
        i=0
        while i<6:
            i=random.randint(0,9)
            x+=str(i)
            i+=1
    return x
    
  

def createplayer(id):
    x=users.find_one({'id':id})
    if x!=None:
        return x
        
def createteam(game):
    id=randomgen(game['teams'])
    return {
        'id':id,            #id тут str, не int!
        'players':[],
        'name':id
    }
        
def creategame(id,message):
   return {
      'id':id,
      'teams':[],
      'turn':1,
      'message':message
   }

def createuser(id,name,username):
   return {
      'id':id,
      'name':name,
      'username':username,
      'shield':100,
      'maxshield':100,
      'lazer':100,
      'maxlazer':100,
      'maxcharge':15,
      'hp':100,
      'maxhp':100,
      'restturns':0,
      'effects':[],
      'team':None
   }

if True:
   print('7777')
   bot.polling(none_stop=True,timeout=600)

