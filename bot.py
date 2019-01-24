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
        if ids['id']==m.chat.id:
            no=1
            game=ids
    if no==0:
        kb=types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(text='Сменить команду', callback_data='teamchoice'))
        msg=bot.send_message(m.chat.id, 'Начинаем сбор игроков! Жмите /tagjoin для вступления в игру.',reply_markup=kb)
        games.append(creategame(m.chat.id,msg))
    else:
        medit('Список игроков ниже.',game['message'].chat.id,game['message'].message_id)
        kb=types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(text='Сменить команду', callback_data='teamchoice'))
        msg=bot.send_message(m.chat.id, editmessage(game),reply_markup=kb)
        game['message']=msg
        

@bot.message_handler(commands=['tagjoin'])
def tagjoin(m):
    yes=0
    for ids in games:
        if ids['id']==m.chat.id:
            yes=1
            game=ids
    if yes==1:
        allplayers=[]
        no=0
        for ids in game['teams']:
            for idss in ids['players']:
                if idss['id']==m.from_user.id:
                    no=1
        if no==0:
            try:
                x=createplayer(m.from_user.id)
                bot.send_message(m.from_user.id, 'Вы успешно присоединились!')
                bot.send_message(m.chat.id, m.from_user.first_name+' присоединился к игре!')
                game['teams'].append(createteam(game))
                game['teams'][len(game['teams'])-1]['players'].append(x)
                kb=types.InlineKeyboardMarkup()
                kb.add(types.InlineKeyboardButton(text='Сменить команду', callback_data='teamchoice'))
                medit(editmessage(game),game['message'].chat.id,game['message'].message_id,reply_markup=kb)
            except:
                bot.send_message(m.chat.id, 'Сначала напишите /start боту @Lazertagbot в личку!')
        else:
            bot.send_message(m.chat.id, m.from_user.first_name+', вы уже в игре!')
        
     
@bot.message_handler(commands=['tagstart'])
def tagstart(m):
    yes=0
    for ids in games:
        if ids['id']==m.chat.id:
            yes=1
            game=ids
    if yes==1:
        if len(game['teams'])>1:
            if game['started']==0:
                game['started']=1
                startgame(game)
        else:
            bot.send_message(m.chat.id, 'Недостаточно команд!')
    else:
        bot.send_message(m.chat.id, 'Нет запущенной игры! Нажмите /preparegame для сбора игроков.')
            
            
@bot.callback_query_handler(func=lambda call:True)
def inline(call): 
    if 'fight' in call.data:
        kb=types.InlineKeyboardMarkup()
        game=None
        player=None
        chat=call.data.split(' ')[2]
        for ids in games:
            if ids['id']==int(chat):
                game=ids
        if game!=None:
            for ids in game['teams']:
                for idss in ids['players']:
                    if idss['id']==call.from_user.id and 'ready' not in idss['effects']:
                        player=idss
        if player!=None:
            if 'shoot' in call.data:
                for ids in game['teams']:
                    if ids['id']!=player['team']:
                        for idss in ids['players']:
                            kb.add(types.InlineKeyboardButton(text='💢'+idss['name'],callback_data='fight target '+chat+' '+str(idss['id'])))
                kb.add(types.InlineKeyboardButton(text='Назад',callback_data='fight back1 '+chat))
                medit('Выберите цель.',player['message'].chat.id,player['message'].message_id,reply_markup=kb)
            
            if 'back1' in call.data:
                sendmenu(player,game,player['team'])
                
            if 'target' in call.data:
                s=[1,2,5]
                s2=[8,10,15]
                b=[]
                b2=[]
                for ids in s:
                    b.append(types.InlineKeyboardButton(text='🔴+'+str(ids)+'%',callback_data='fight charge '+chat+' '+str(ids)))
                for ids in s2:
                    b2.append(types.InlineKeyboardButton(text='🔴+'+str(ids)+'%',callback_data='fight charge '+chat+' '+str(ids)))
                kb.add(b[0],b[1],b[2])
                kb.add(b2[0],b2[1],b2[2])
                medit('Выберите силу заряда. Текущая сила: '+str(player['currentcharge'])+'%',player['message'].chat.id,player['message'].message_id,reply_markup=kb)
                
                
                
                
        


def startgame(game):
    for ids in game['teams']:
        team=ids['id']
        for idss in ids['players']:
            idss['team']=team
    for ids in game['teams']:
        for idss in ids['players']:
            sendmenu(idss,game,idss['team'])
    bot.send_message(game['id'],'Начинаем перестрелку! Приготовьте свои лазер-пушки и энергетические щиты и переключайтесь в личку бота!')
            
    
def sendmenu(player,game,team):
    text='Ваша команда:\n\n'
    for ids in game['teams']:
        if ids['id']==team:
            team=ids
    for ids in team['players']:
        text+=ids['name']+':\n'+'♥️:'+str(ids['hp'])+'%, 🔵:'+str(ids['shield'])+'%, 🔴:'+str(ids['lazer'])+'%\n\n'
    kb=types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='🔴Стрельба', callback_data='fight shoot '+str(game['id'])),types.InlineKeyboardButton(text='🔵Защита', callback_data='fight def '+str(game['id'])))
    if player['message']==None:
        msg=bot.send_message(player['id'],text+'Выберите действие.',reply_markup=kb)
        player['message']=msg
    else:
        medit(text+'Выберите действие.',player['message'].chat.id,player['message'].message_id,reply_markup=kb)
    
    
    
def medit(message_text,chat_id, message_id,reply_markup=None,parse_mode=None):
    return bot.edit_message_text(chat_id=chat_id,message_id=message_id,text=message_text,reply_markup=reply_markup,
                                 parse_mode=parse_mode)  


def editmessage(game):
    text='Начинаем сбор игроков! Жмите /tagjoin для вступления в игру.\n\n'
    for ids in game['teams']:
        t=ids
        text+='Команда '+t['name']+':\n'
        i=0
        for idss in t['players']:
            player=idss
            if i!=len(t['players'])-1:
                symbol='┞'
            else:
                symbol='┕'
            text+=symbol+player['name']+'\n'
            i+=1
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
        while i<3:
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
      'started':0,
      'message':message
   }

def createdamager(player,damage):
    return {
        'id':player['id'],
        'damage':damage
    }

def createuser(id,name,username):
   return {
      'id':id,
      'name':name,
      'username':username,
      'dead':0,
      'shield':100,
      'maxshield':100,
      'lazer':100,
      'maxlazer':100,
      'maxcharge':15,
      'currentlazer':0,
      'currentdef':0,
      'hp':100,
      'maxhp':100,
      'restturns':0,
      'effects':[],
      'team':None,
      'action':None,
      'target':None,
      'message':None,
      'damagers':[]
   }

if True:
   print('7777')
   bot.polling(none_stop=True,timeout=600)

