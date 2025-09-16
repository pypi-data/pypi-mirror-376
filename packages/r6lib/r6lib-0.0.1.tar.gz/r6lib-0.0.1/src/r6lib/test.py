import r6
import sys

op = r6.Operator.get(r6.Operator.DefendOperatorType.SMOKE)
random_op = op.randomize()
weapon = random_op.get_primary()
attach_type = r6.Weapon.Attachment.BarrelAttachment.EXT

print(f' ! {weapon.name}')
print(f'scope: {weapon.get_scope()}, barrel: {weapon.get_barrel()}, grip: {weapon.get_grip()}, underbarrel: {weapon.get_underbarrel()}')

print(f'pre-equip damage: {weapon.damage}, ext equip? {weapon.has_attachment(attach_type)}')
print(f'mods: {weapon.get_available_modifiers()}')

if not weapon.allows_attachment_category(attach_type.get_category()):
    print(f'barrels not allowed on {weapon.name} :(')
    exit(0)

if not weapon.allows_attachment(attach_type):
    print(f'ext not allowed on {weapon.name} :(')
    sys.exit(0)

weapon.equip(attach_type)
print(f'post-equip damage: {weapon.damage}, ext equip? {weapon.has_attachment(attach_type)}')
print(f'mods: {weapon.get_available_modifiers()}')

weapon.equip(r6.Weapon.Attachment.BarrelAttachment.FLASH)
print(f'post-unequip damage: {weapon.damage}, ext equip? {weapon.has_attachment(attach_type)}')
print(f'mods: {weapon.get_available_modifiers()}')

print(f'\nexport: {random_op.export()}')