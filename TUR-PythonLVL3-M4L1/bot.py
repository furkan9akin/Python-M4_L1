import discord
from discord.ext import commands, tasks
from logic import DatabaseManager, hide_img
from config import TOKEN, DATABASE
import cv2
import numpy as np
import os
from logic import *
from math import sqrt, ceil, floor


intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

manager = DatabaseManager(DATABASE)
manager.create_tables()



def create_collage(image_paths):
    images = []
    for path in image_paths:
        image = cv2.imread(path)
        images.append(image)

    num_images = len(images)
    num_cols = floor(sqrt(num_images)) # Satır başına düşen resim sayısını belirleme
    num_rows = ceil(num_images/num_cols)  # Sütun başına düşen resim sayısını belirleme
    # Boş bir kolaj oluşturma
    collage = np.zeros((num_rows * images[0].shape[0], num_cols * images[0].shape[1], 3), dtype=np.uint8)
    # Resimleri kolaj üzerine yerleştirme
    for i, image in enumerate(images):
        row = i // num_cols
        col = i % num_cols
        collage[row*image.shape[0]:(row+1)*image.shape[0], col*image.shape[1]:(col+1)*image.shape[1], :] = image
    return collage


m = DatabaseManager(DATABASE)
info = m.get_winners_img("user_id")
prizes = [x[0] for x in info]
image_paths = os.listdir('img')
image_paths = [f'img/{x}' if x in prizes else f'hidden_img/{x}' for x in image_paths]
collage = create_collage(image_paths)

cv2.imshow('Collage', collage)
cv2.waitKey(0)
cv2.destroyAllWindows()

# Kullanıcı kaydı için bir komut
@bot.command()
async def start(ctx):
    user_id = ctx.author.id
    if user_id in manager.get_users():
        await ctx.send("Zaten kayıtlısınız!")
    else:
        manager.add_user(user_id, ctx.author.name)
        await ctx.send("""Merhaba! Hoş geldiniz! Başarılı bir şekilde kaydoldunuz! Her dakika yeni resimler alacaksınız ve bunları elde etme şansınız olacak! Bunu yapmak için “Al!” butonuna tıklamanız gerekiyor! Sadece “Al!” butonuna tıklayan ilk üç kullanıcı resmi alacaktır! =)""")

# Resim göndermek için zamanlanmış bir görev
@tasks.loop(minutes=1)
async def send_message():
    for user_id in manager.get_users():
        prize_id, img = manager.get_random_prize()[:2]
        hide_img(img)
        user = await bot.fetch_user(user_id) 
        if user:
            await send_image(user, f'hidden_img/{img}', prize_id)
        manager.mark_prize_used(prize_id)

async def send_image(user, image_path, prize_id):
    with open(image_path, 'rb') as img:
        file = discord.File(img)
        button = discord.ui.Button(label="Al!", custom_id=str(prize_id))
        view = discord.ui.View()
        view.add_item(button)
        await user.send(file=file, view=view)

@bot.event
async def on_interaction(interaction):
    if interaction. type == discord. InteractionType. component :
        custom_id = interaction. data[ 'custom_id' ]
        user_id = interaction.user.id
            
        if manager.get_winners_count(custom_id) < 3:#kazanan_sayısı# () < 3:
            res = manager.ad_winner(user_id , custom_id)#bir_kazanan_ekle# ()
            if res:
                img = manager.get_prize_img(custom_id)#ödül_resmi_al# ()
                with open(f'img/[img]', 'rb') as photo:
                    file = discord. File(photo)
                    await interaction.response.send_message(file=file, content="Tebrikler, resmi aldınız!")
            else:
                await interaction.response.send_message(content="Bu resme zaten sahipsiniz!", ephemeral=True)
        else:
            await interaction.response.send_message(content="Maalesef, birisi bu resmi çoktan aldı ... ", ephemeral=True)

@bot.event
async def on_ready():
    print(f'{bot.user} olarak giriş yapıldı!')
    if not send_message.is_running():
        send_message.start()

bot.run(TOKEN)

bot.run(TOKEN)
