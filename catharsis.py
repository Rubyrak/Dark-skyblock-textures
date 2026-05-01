import os
import shutil
import json
from pathlib import Path

# --- CONFIGS ---
DIR_ORIGIN = Path("assetss")
DIR_DESTINY = Path(".")
# Folders
FIRM_ISLAND = "dms_ghosts" # Original zone
CATHA_ISLAND_ZONE = "ghosts" # Target zone

CATHA_AREA = f"dms:{CATHA_ISLAND_ZONE}"

# I don't like this...
SLAB_EXCEPTIONS = {
    "polished_blackstone_brick_slab": "polished_blackstone_bricks",
    "stone_brick_slab": "stone_bricks",
    "end_stone_brick_slab": "end_stone_bricks",
    "nether_brick_slabs": "nether_bricks", # se que vas a faltar perro
    "birch_slab": "birch_planks",
    "oak_slab": "oak_planks",
    "spruce_slab": "spruce_planks",
    "dark_oak_slab": "dark_oak_planks",
    "jungle_slab": "jungle_planks",
    "acacia_slab": "acacia_planks"
}

def get_target_file():
    if FIRM_ISLAND.startswith("zz_"):
        real_name = FIRM_ISLAND.replace("zz_", "", 1)
        return DIR_ORIGIN / "dms" / "overrides" / "blocks" / f"{real_name}.json"
    else:
        return DIR_ORIGIN / "firmskyblock" / "overrides" / "blocks" / f"{FIRM_ISLAND}.json"

def generate_island_keywords(island_file):
    keywords = set()
    with open(island_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    for _, destination_block in data.get("replacements", {}).items():
        id_dest = destination_block.split(":")[-1] # ex: dark_sandstone_stairs
        keywords.add(id_dest)

        # Add base for uncommon textures (ex: base texture from stairs)
        base = id_dest.replace("_stairs", "").replace("_slab", "").replace("_wall", "").replace("_frame", "").replace("_layer", "").replace("_block", "")
        keywords.add(base)

        if "snow" in id_dest:
            snow_base = id_dest.split("_snow")[0] + "_snow"
            keywords.add(snow_base)
        
    return keywords, data

def step_1_and_2_copy_only_necessary(keywords):
    print(f"\n--- Step 1-2: Copied assets from '{FIRM_ISLAND}' ---")
    namespaces_origin = ["dms", "firmskyblock", "minecraft"] # Where to copy from (main folder)
    bl_types_asset = ["textures/block", "models/block"] # Where those will be copied (target folder)

    # 1. LEAKED COPIES
    copied_files = 0
    for ns in namespaces_origin:
        for bl_type in bl_types_asset:
            origin_route = DIR_ORIGIN / ns / bl_type
            if not origin_route.exists():
                continue
                
            for origin_file in origin_route.rglob("*.*"):
                if origin_file.is_file():
                    if any(pc in origin_file.name for pc in keywords):
                        relative_route = origin_file.relative_to(origin_route)
                        destiny_file = DIR_DESTINY / "assets" / "dms" / bl_type / relative_route
                        
                        destiny_file.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(origin_file, destiny_file)
                        copied_files += 1

    print(f"Exact copied files: {copied_files} (models and textures).")

    # 2. UPDATING REFERENCES IN COPIED MODELS
    new_models_route = DIR_DESTINY / "assets" / "dms" / "models" / "block"
    if new_models_route.exists():
        for file_json in new_models_route.rglob("*.json"):
            with open(file_json, 'r', encoding='utf-8') as f:
                content = f.read()

            # Changed references for copied files
            content = content.replace('"firmskyblock:block/', '"dms:block/')
            with open(file_json, 'w', encoding='utf-8') as f:
                f.write(content)

def process_virtual_block_state(ns_dest, id_dest):
    vbs_route = DIR_DESTINY / "assets" / ns_dest / "catharsis" / "virtual_block_states"
    vbs_route.mkdir(parents=True, exist_ok=True)

    file_vbs = vbs_route / f"{id_dest}.json"
    if file_vbs.exists():
        return
        
    old_bs_firm_route = DIR_ORIGIN / "firmskyblock" / "blockstates" / f"{id_dest}.json" # Old BlockState Firmament route
    old_bs_mc_route = DIR_ORIGIN / "minecraft" / "blockstates" / f"{id_dest}.json" # Old BlockState Minecraft route --  No uses?¿¿?
    
    complete_bs_found = None
    if old_bs_firm_route.exists():
        complete_bs_found = old_bs_firm_route # Old BlockState Firmament
    elif old_bs_mc_route.exists():
        complete_bs_found = old_bs_mc_route # Old BlockState Minecraft

    if complete_bs_found:
        with open(complete_bs_found, 'r', encoding='utf-8') as f:
            content = f.read()
        content = content.replace('"firmskyblock:block/', '"dms:block/')
        with open(file_vbs, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  [+] Complex VBS Applied from Firmament: {ns_dest}:{id_dest}") # Complex block state (ex: stairs)
    
    else:
        is_stairs = id_dest.endswith("_stairs")
        is_slab = id_dest.endswith("_slab")
        is_wall = id_dest.endswith("_wall")
        is_wood = id_dest.endswith("_wood")
        
        if is_stairs or is_slab or is_wall or is_wood:
            template_name = ""
            if is_stairs: template_name = "template_stairs.json"
            elif is_slab: template_name = "template_slab.json"
            elif is_wall: template_name = "template_wall.json"
            elif is_wood: template_name = "template_wood.json"
            
            template_path = DIR_ORIGIN / "minecraft" / "blockstates" / template_name
            
            if template_path.exists():
                with open(template_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                model_namespace = "minecraft" if ns_dest == "minecraft" else "dms"

                if id_dest in SLAB_EXCEPTIONS:
                    base_block = SLAB_EXCEPTIONS[id_dest]
                else:
                    base_block = id_dest.replace("_slab", "").replace("_stairs", "").replace("_wall", "").replace("_wood", "")
                
                content = content.replace("__NAMESPACE__", model_namespace)
                content = content.replace("__BLOCK__", id_dest)
                content = content.replace("__BLOCK_BASE__", base_block)
                
                with open(file_vbs, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"  [+] Template VBS Generated for: {ns_dest}:{id_dest}") # Template complex block state
            else:
                print(f"  [!] Missing template '{template_name}' for {id_dest}") # Needed¿?
                
        else:
            model_namespace = "minecraft" if ns_dest == "minecraft" else "dms"
            content_vbs = {
                "variants": {
                    "": { "model": f"{model_namespace}:block/{id_dest}" }
                }
            }
            with open(file_vbs, 'w', encoding='utf-8') as f:
                json.dump(content_vbs, f, indent=4)
            print(f"  [+] Simple VBS Generated: {ns_dest}:{id_dest}") # Simple block state

def step_3_migrate_logic(island_data):
    print(f"\n--- Step 3: Migrating '{FIRM_ISLAND}' ---")
    
    modes = island_data.get("modes", [])
    if not modes:
        print("No 'modes' found.")
        return
        
    replacements = island_data.get("replacements", {})
    
    for original_block, destination_block in replacements.items():
        ns_orig, id_orig = original_block.split(":")
        ns_dest, id_dest = destination_block.split(":")

        if ns_dest == "firmskyblock": ns_dest = "dms" # Lo estaba guardando todo en assets/firmament por el dinamismo......
        
        process_virtual_block_state(ns_dest, id_dest)

        # Create replacement for target island
        replace_route = DIR_DESTINY / CATHA_ISLAND_ZONE / "assets" / CATHA_ISLAND_ZONE / "catharsis" / "block_replacements" / ns_orig
        replace_route.mkdir(parents=True, exist_ok=True)
        
        replace_file = replace_route / f"{id_orig}.json"
        content_repl = {
            "type": "per_area",
            "entries": {
                CATHA_AREA: {
                    "type": "redirect",
                    "virtual_state": f"{ns_dest}:{id_dest}"
                }
            }
        }
        
        with open(replace_file, 'w', encoding='utf-8') as f:
            json.dump(content_repl, f, indent=4)

if __name__ == "__main__":
    print(f"Target island: {FIRM_ISLAND}")
    
    target_file = get_target_file()

    if not target_file.exists():
        print(f"¡ERROR! Couldn't find {target_file}")
    else:
        print(f"File found at: {target_file}")
        keywords, island_data = generate_island_keywords(target_file)
        
        step_1_and_2_copy_only_necessary(keywords)
        step_3_migrate_logic(island_data)