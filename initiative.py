from interactions import Extension, listen, slash_command, SlashContext, OptionType, slash_option
from interactions.api.events import Component
from interactions import ActionRow, Button, ButtonStyle
import random
import d20

guild_initiative_orders = {}
last_init_message = {}

class Initiative_Handler(Extension):
    # Join Init Order Function, adds a user to the queue, and sorts it but highest init
    # ===================================================================================
    @slash_command(name="join", description="auto rolls and joins the user into the initiative order")
    @slash_option(
        name="mod",
        description="initiative modifier, ex: '1' or '1d4 + 1",
        required=False,
        opt_type=OptionType.STRING
    )
    async def join_command(self, ctx: SlashContext, mod: str="0"):
        roll = random.randint(1, 20)
        calculated_mod = d20.roll(str(mod)).total
        
        # Get the guild-specific initiative order or create an empty list if it doesn't exist
        guild_id = ctx.guild.id
        initiative_order = guild_initiative_orders.get(guild_id, [])
        
        # Check if the user is already in the initiative order
        user_index = next((index for index, participant in enumerate(initiative_order) if participant.get('user') == ctx.author), None)
        
        if user_index is not None:
            # Remove the user's previous entry
            initiative_order.pop(user_index)
        
        participant_info = {
            "user": ctx.author,
            "initiative": roll + calculated_mod,
            "modifier": calculated_mod
        }
        
        initiative_order.append(participant_info)
        initiative_order.sort(key=lambda x: (x["initiative"], x.get("modifier", 0)), reverse=True)

        
        # Store the updated initiative order back in the dictionary
        guild_initiative_orders[guild_id] = initiative_order
        await ctx.send(f"{ctx.author.mention} has joined the fray!\n" +
                        f"🎲 = **{roll + calculated_mod}**\n" + 
                        f"1d20({roll}) + {calculated_mod}")

    # ===================================================================================


    #NPC Join Function
    # ===================================================================================
    @slash_command(name="npc-join", description="Add an NPC to the initiative order")
    @slash_option(
        name="name",
        description="Name of the NPC",
        required=True,
        opt_type=OptionType.STRING
    )
    @slash_option(
        name="mod",
        description="Initiative modifier (optional)",
        required=False,
        opt_type=OptionType.STRING
    )
    async def npc_join_command(self, ctx: SlashContext, name: str, mod: str="0"):
        # Get the guild-specific initiative order or create an empty list if it doesn't exist
        guild_id = ctx.guild.id
        initiative_order = guild_initiative_orders.get(guild_id, [])

        calculated_mod = d20.roll(str(mod)).total
        
        # Check if the NPC is already in the initiative order
        npc_index = next((index for index, participant in enumerate(initiative_order) if participant.get('name') == name), None)
        
        if npc_index is not None:
            # Remove the NPC's previous entry
            initiative_order.pop(npc_index)
        
        # Roll initiative for the NPC, don't need
        roll = random.randint(1, 20)
        
        npc_info = {
            "name": name,
            "initiative": roll + calculated_mod,
            "modifier": calculated_mod
        }
        
        initiative_order.append(npc_info)
        initiative_order.sort(key=lambda x: x["initiative"], reverse=True)
        
        # Store the updated initiative order back in the dictionary
        guild_initiative_orders[guild_id] = initiative_order
        
        await ctx.send(f"NPC '{name}' has joined the fray!\n" 
                       + f"🎲 = **{roll + calculated_mod}**")
    # ===================================================================================


    #Custom Join Function
    # ===================================================================================
    @slash_command(name="custom-join", description="join the initiative with a custom value")
    @slash_option(
        name="roll",
        description="Initiative Score",
        required=True,
        opt_type=OptionType.INTEGER
    )
    @slash_option(
        name="mod",
        description="Initiative Score",
        required=False,
        opt_type=OptionType.INTEGER
    )
    async def custom_join_command(self, ctx: SlashContext, roll: int, mod: int=0):      # Get the guild-specific initiative order or create an empty list if it doesn't exist
        guild_id = ctx.guild.id
        initiative_order = guild_initiative_orders.get(guild_id, [])

        # Check if the user is already in the initiative order
        user_index = next((index for index, participant in enumerate(initiative_order) if participant.get('user') == ctx.author), None)
        
        if user_index is not None:
            # Remove the user's previous entry
            initiative_order.pop(user_index)
        
        participant_info = {
            "user": ctx.author,
            "initiative": roll + mod,
            "modifier": mod
        }
        
        initiative_order.append(participant_info)
        initiative_order.sort(key=lambda x: (x["initiative"], x.get("modifier", 0)), reverse=True)

        
        # Store the updated initiative order back in the dictionary
        guild_initiative_orders[guild_id] = initiative_order
        
        await ctx.send(f"{ctx.author.mention} has joined the fray!\n" +
                       f"🎲 = **{roll + mod}**" 
                       f"1d20({roll}) + [{mod}]")
    # ===================================================================================
    

    # Components
    components: list[ActionRow] = [
        ActionRow(
            Button(
                custom_id="next_init_button",
                style=ButtonStyle.GREEN,
                label="NEXT",
            ),
            Button(
                custom_id="clear_init_button",
                style=ButtonStyle.BLUE,
                label="CLEAR",
            )
        )
    ]


    # Show Init Order Function, iterates through the current order and prints
    # ===================================================================================
    @slash_command(name="display", description="Display and cycle through the current initiative order")
    async def display_command(self, ctx: SlashContext):
        initiative_order = guild_initiative_orders.get(ctx.guild.id, [])
        
        if initiative_order:
            order_text = "\n".join([f"{participant['name'] if 'name' in participant else participant['user'].display_name} | **{participant['initiative']}**" for participant in initiative_order])
            message = await ctx.send(f"**__Initiative Order:__**\n{order_text}", components=self.components)
            
            # Store the message ID as the last_init_message for the guild
            last_init_message[ctx.guild.id] = message.id
        else:
            await ctx.send("🐉 Initiative order is empty. Use `/join` or `/npc-join` to add participants.")

    # ===================================================================================


    @listen()
    async def on_component(self, event: Component):
        ctx = event.ctx
        guild_id = ctx.guild.id
        
        match ctx.custom_id:
            case "next_init_button":
                # Get the guild-specific initiative order or create an empty list if it doesn't exist
                initiative_order = guild_initiative_orders.get(guild_id, [])
                
                if initiative_order:
                    current_participant = initiative_order[0]  # Get the current participant without popping

                    if len(initiative_order) > 1:
                        next_participant = initiative_order[1] if len(initiative_order) > 1 else None  # Get the next participant without popping
                        message = await ctx.send(
                            f"⚔️ {current_participant['name'] if 'name' in current_participant else current_participant['user'].mention} is up! \n" +
                            f"🛡 {next_participant['name'] if 'name' in next_participant else next_participant['user'].mention} *is on deck!* \n"
                              + f"\n__Current Initiative:__ \n{self.display_init(guild_id)}",
                            components=self.components,
                        )
                        current_participant = initiative_order.pop(0)  # Pop the current participant from the front
                        initiative_order.append(current_participant)  # Move them to the back # Pop the current participant from the front AFTER sending the message
                        await ctx.delete(message=last_init_message[guild_id])
                        # Update the last_init_message for the guild
                        last_init_message[ctx.guild.id] = message.id

                    else:
                        message = await ctx.send(
                            f"⚔️ {current_participant['name'] if 'name' in current_participant else current_participant['user'].mention} is up! The initiative order is empty.",
                            components=self.components,
                        )
                        await ctx.delete(message=last_init_message[guild_id])
                        last_init_message[ctx.guild.id] = message.id
                else:
                    await ctx.send("The initiative order is empty.")
            case "clear_init_button":
                initiative_order = guild_initiative_orders.get(guild_id, [])
                initiative_order.clear()
                guild_initiative_orders[guild_id] = initiative_order
                message = await ctx.send("Initiative order has been cleared")
                await ctx.delete(message=last_init_message[guild_id])
                # Clear the last_init_message for the guild
                last_init_message[ctx.guild.id] = None

    # Print the initiative order (Helper Function)
    # ===================================================================================
    def display_init(self, guild_id):
        initiative_order = guild_initiative_orders.get(guild_id, [])
        return "\n".join(f"~ {participant['name'] if 'name' in participant else participant['user'].display_name} | **{participant['initiative']}**" for participant in initiative_order)