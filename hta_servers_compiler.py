import os
import yaml
from lxml import etree

from easygui import diropenbox


version='1.0'

config = None
debug = False
declaration = '<?xml version="1.0" encoding="windows-1251" standalone="yes"?>'
base_gameobjects = [ 
    'gameobjects.xml',
    'bigguns.xml',
    'gadgets.xml',
    'giantguns.xml',
    'mortar.xml',
    'plasma.xml',
    'questitems.xml',
    'rockets.xml',
    'sideguns.xml',
    'smallguns.xml',
    'thunderbolt.xml',
    'vehicleparts.xml',
    'vehiclescrotch.xml',
    'crotchguns.xml',
    'wares.xml'
]
used_gameobjects = [
    'breakableobjects.xml',
    'bosses.xml',
    'towns.xml',
]
gameobjects = '../../gamedata/gameobjects/'
dynscene = 'dynamicscene.xml'
world = 'world.xml'
strings = 'strings.xml'
default_animmodels = {
    'cargo',
    'box',
    'cub',
    'conteiner',
    'mask_hero',
    'point',
    'dweller_player'
}
sounds = '../../sounds/'
servers_animmodels_file = 'data\models\AnimModels.xml'

try:
    with open('servcomp.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
        if 'debug' in config: debug = config['debug']
        if 'gameobjects_save_all' in config: base_gameobjects = config['gameobjects_save_all']
        if 'gameobjects_save_only_used' in config: used_gameobjects = config['gameobjects_save_only_used']
        if 'gameobjects' in config: gameobjects = config['gameobjects']
        if 'dynscene' in config: dynscene = config['dynscene']
        if 'world' in config: world = config['world']
        if 'strings' in config: strings = config['strings']
        if 'default_animmodels' in config: default_animmodels = config['default_animmodels']
        if 'sounds' in config: sounds = config['sounds']
        if 'declaration' in config: declaration = config['declaration']
        if 'servers_animmodels_file' in config: servers_animmodels_file = config['servers_animmodels_file']
except FileNotFoundError as e:
    print('🚫 файл конфигурации не найден')

def get_recursive_models(root, tag, node_name):
    model_names = []
    for node in root.findall(node_name):
        model_name = node.get(tag)
        if model_name and not model_name in model_names:
            model_names.append(model_name)
            if debug: print(f'    • Получен {model_name}')
        else:
            try:
                child = get_recursive_models(node, tag = tag, node_name = node_name)
                if child:
                    model_names += child
            except:
                print(f'      🚫 Для дочерних объектов {node} ({node_name}) не найден параметр {tag}')
    return model_names

def get_recursive_models_from_gameobjects(root, tag, prototypes_used = None):
    model_names = []
    for node in root:
        model_name = node.get(tag)
        if model_name:
            if not prototypes_used:
                model_names.append(model_name)
                resource_type = node.get('ResourceType')
                if resource_type and 'GUN' in resource_type:
                    if debug: print(f'      • Найден объект {resource_type}')
                    model_names.append(f'{model_name}gun')
                    if debug: print(f'      • Получен {model_name}gun')
                if debug: print(f'      • Получен {model_name}')
            else:
                if node.get('Name') in prototypes_used:
                    model_names.append(model_name)
                    if debug: print(f'      • Получен {model_name}')
        else:
            try:
                child = get_recursive_models_from_gameobjects(node, tag = tag, prototypes_used = prototypes_used)
                if child:
                    model_names += child
            except:
                print(f'      🚫 Для дочерних объектов {node} не найден параметр {tag}')
    return model_names

def process_nodes(xml, folder, tag, nodename):
    xml_tree = etree.parse(f'{folder}\\{xml}')
    xml_root = xml_tree.getroot()
    print(f'  🔬 Обработка моделей в {xml}...')
    xml_models = get_recursive_models(xml_root, tag, nodename)
    print(f'    🧹 Удаление возможных дубликатов...')
    xml_models = list(set(xml_models))
    return xml_models

def process_prototypes(gameobjects_filepath, prototypes_used = None):
    try:
        models = []
        xml = etree.parse(gameobjects_filepath)
        root = xml.getroot()
        for model in ['ModelFile', 'BrokenModel', 'DestroyedModel', 'GateModelFile', 'SuspensionModelFile']:
            models += get_recursive_models_from_gameobjects(root, model, prototypes_used)
        return models
    except FileNotFoundError as e:
        print(f'    🚫 Не найден файл {gameobjects_file}')

print(f'Вас приветствует 🦐   HTA servers.xml Compiler ver. {version} \n')
map_folder = diropenbox(
    msg = 'Выберите папку нужной карты.',
    title = 'Выбор карты'
)
print(f'  🍞 Компиляция servers.xml: {map_folder}')


world_models = process_nodes(world, map_folder, 'id', 'Node')
strings_models = process_nodes(strings, map_folder, 'modelName', 'string')
dynscene_models = process_nodes(dynscene, map_folder, 'ModelName', 'Object')

dynscene_tree = etree.parse(f'{map_folder}\\{dynscene}')
dynscene_root = dynscene_tree.getroot()
print(f'  🚚 Обработка прототипов в {dynscene}...')
dynscene_prototypes = get_recursive_models(dynscene_root, 'Prototype', 'Object')
print(f'    🧹 Удаление возможных дубликатов...')
dynscene_prototypes = list(set(dynscene_prototypes))
print(f'  🏠 Обработка прототипов в GameObjects:')
gameobjects_models = []
gameobjects_path = f'{os.path.abspath(os.path.join(map_folder, gameobjects))}'
if used_gameobjects:
    print(f'  🤔 Сохранение списка используемых прототипов...')
    for gameobjects_file in used_gameobjects:
        print(f'    🔧 Обрабатывается {gameobjects_file}:')
        gameobjects_models += process_prototypes(f'{gameobjects_path}\\{gameobjects_file}', dynscene_prototypes)
            
if base_gameobjects:
    print(f'  😎 Сохранение списка базовых прототипов...')
    for gameobjects_file in base_gameobjects:
        print(f'    🔧 Обрабатывается {gameobjects_file}:')
        gameobjects_models += process_prototypes(f'{gameobjects_path}\\{gameobjects_file}')
print(f'    🧹 Удаление возможных дубликатов...')
gameobjects_models = list(set(gameobjects_models))

servers_models = world_models + strings_models + dynscene_models + gameobjects_models + default_animmodels

print(f'    🛁 Окончательная очистка...')
servers_models = list(set(servers_models))
print(f'  💽 Получено {len(servers_models)} объектов класса Animated Model!')

sounds_path = f'{os.path.abspath(os.path.join(map_folder, sounds))}'
servers_sounds = process_nodes('sounds.xml', sounds_path, 'id', 'model')
print(f'  💽 Получено {len(servers_sounds)} объектов класса Sounds!')

new_xml_servers_root = etree.Element('Servers')
xml_animated_models_server = etree.SubElement(new_xml_servers_root, 'AnimatedModelsServer')
for model_id in servers_models:
    item = etree.SubElement(xml_animated_models_server, 'Item')
    item.set('id', model_id)
    item.set('file', servers_animmodels_file)
xml_sounds_server = etree.SubElement(new_xml_servers_root, 'SoundsServer')
for sound_id in servers_sounds:
    item = etree.SubElement(xml_sounds_server, 'Item')
    item.set('id', sound_id)

print(f'  🔧 Идёт сборка servers.xml!..')
new_servers = etree.ElementTree(new_xml_servers_root)
with open('servers.xml', 'wb') as f:
    new_servers.write(
        f, 
        encoding='windows-1251', 
        xml_declaration=True, 
        pretty_print=True
    )
print(f'  💾 Файл сохранён в текущей директории.')
input('Нажмите что угодно для продолжения...')
