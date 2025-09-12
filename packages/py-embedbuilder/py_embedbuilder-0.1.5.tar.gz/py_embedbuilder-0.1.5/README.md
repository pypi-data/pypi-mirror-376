# Discord EmbedBuilder

Does a lot of shit and simplifies discord's annoying and lengthy embed creation process.

## Installation
```bash
pip install py-embedbuilder
```
From there you can just..

## Example
```py
import discord
from discord.ext import commands
from embedbuilder import EmbedBuilder

@bot.command(name="example")
async def example(ctx):
    msg = await EmbedBuilder(ctx) \
        .set_title("Welcome!") \
        .set_description("This is a basic embed") \
        .set_color(discord.Color.blue()) \
        .send()
```

or

```py
@bot.command(name="example")
async def example(ctx):
    builder = EmbedBuilder(ctx)
    messages = await (builder
                     .set_title("Welcome!")
                     .set_description("This is a basic embed")
                     .set_color(discord.Color.blue())
                     .send())
```

These both do the exact same thing it's just a matter of preference.

## "Quick" explanation of everything you can do

? denotes optional inputs and **SHOULD NOT** be included in the actual function. If there is no ? it's a required field.

### Basic stuff
```py
.set_title("Your title here")
.set_description("Whatever you want to say")
.set_color(discord.Color.red())  # or any color
.set_url("https://example.com")  # makes the title clickable
```

### Author details
Author details (author name, author icon url, author url) are incredibly simple.
```py
.set_author("Cheap Credits", ?icon_url="https://example.com/img.png", ?url="https://cheap.ypuf.xyz")
```

### Footer details
```py
.set_footer("Visit my site!", ?icon_url="https://example.com/img.png")
```

### Fields
These are just normal field inputs so it's title, description and then inline: true/false
```py
.add_field("Look at this number", "17", inline=True)
.add_field("Another field", "Some value", inline=False)
```

### Images and thumbnails
```py
.set_thumbnail("https://example.com/small_image.png")  # small image in top right
.set_image("https://example.com/big_image.png")       # big image at bottom
```

### Files and attachments
```py
.set_file_path("./my_image.png")  # attach a local file
.add_file(discord.File("another_file.txt"))  # or add discord files directly
```

### Message content (outside the embed)
```py
.set_content("This text appears above the embed")
```

### Timestamps
```py
.set_timestamp()  # uses current time
.set_timestamp(some_datetime_object)  # or your own time
.set_timezone('America/New_York')  # change timezone if needed
```

## For slash commands
Works exactly the same but pass the interaction instead of ctx:
```py
@bot.slash_command()
async def slash_example(interaction):
    await EmbedBuilder(interaction) \
        .set_title("Slash command embed") \
        .set_ephemeral(True) \
        .send()  # only the user who ran the command can see it
```

## Long descriptions? No problem
If your description is too long, it'll automatically split it into multiple embeds:
```py
really_long_text = "Lorem ipsum..." * 1000

await EmbedBuilder(ctx) \
    .set_title("Long ass message") \
    .set_description(really_long_text) \
    .send()  # automatically creates multiple embeds
```

## Pagination for fancy stuff
Want actual page navigation? Enable pagination:
```py
builder = EmbedBuilder(ctx).enable_pagination()

# Add custom pages
builder.add_page(title="Page 1", description="First page content")
builder.add_page(title="Page 2", description="Second page content")
builder.add_page(title="Page 3", description="Third page content")

await builder.send()  # creates navigation buttons
```

## Other useful shit

### Reply to messages
```py
.set_reply(True)   # default behavior (if you're sending to a specific channel it won't reply to the user anyway)
.set_reply(False)  # don't reply, just send normally
```

### Auto-delete messages
```py
.set_delete_after(30)  # deletes after 30 seconds
```

### Edit existing messages instead of sending new ones
```py
old_message = await EmbedBuilder().... # any old embedbuilder function or any old embed at all
await EmbedBuilder(ctx) \
    .edit_message(old_message) \
    .set_title("Done!") \
    .send()
```

### Forums and threads
(IF YOURE CREATING A FORUM) Forums are a little bit "complicated" with a specific call being required.
If the forum already exists, it acts as a normal channel.
```py
await EmbedBuilder(forum_channel) \
    .create_forum_thread(
        name="Bug report 2077!",
        ?content="Pls help johnny silverhand is in my head." # Optional, defaults to embed content.
    ) \
    .set_title("Please patch!!") \
    .set_description("So this would actually appear as embedded text") \
    .send()
```
(IF YOU'RE CREATING A THREAD) You have a lot of input options for this.
If the thread already exists, it acts as a normal channel.
```py
await EmbedBuilder(ctx) \
    .set_title("Any embed title") \
    .set_description("Any embed description") \
    .create_thread("New thread!", ?auto_archive_duration=10080, ?reason="I felt like creating one lol xd") \ # Duration is in minutes.
    .send()
```
I'm pretty sure auto_archive_duration has to be very rigid times but I'm not entirely sure of that.
Don't pass in `None` to auto_archive_duration.

## That's basically it
The library handles all the annoying Discord limits and validation for you. Just chain the methods you want and call `.send()` at the end.

If something breaks, it'll probably tell you what went wrong instead of just dying silently like Discord's API likes to do.
