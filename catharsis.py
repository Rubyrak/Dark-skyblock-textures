import os
import shutil
import json
from pathlib import Path

# --- CONFIGS ---
DIR_ORIGIN = Path("assetss")
DIR_DESTINY = Path(".")
# Folders
FIRM_ISLAND = "aa_dms_end"
CATHA_ISLAND = "the_end"

def generate_island_keywords(island_file):
    keywords = set()
    with open(island_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    for _, destination_block in data.get("replacements", {}).items():
        id_dest = destination_block.split(":")[-1] # ex: dark_sandstone_stairs
        keywords.add(id_dest)
        
        # Add base for uncommon textures (ex: base texture from stairs)
        base = id_dest.replace("_stairs", "").replace("_slab", "").replace("_wall", "").replace("_frame", "")
        keywords.add(base)
        
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
    print("Updated references of filtered models.")

def process_virtual_block_state(ns_dest, id_dest, vbs_route):
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
        print(f"  [+] Complex VBS: dms:{id_dest}") # Complex block state (ex: stairs)
    else:
        model_namespace = "minecraft" if ns_dest == "minecraft" else "dms"
        content_vbs = {
            "variants": {
                "": { "model": f"{model_namespace}:block/{id_dest}" }
            }
        }
        with open(file_vbs, 'w', encoding='utf-8') as f:
            json.dump(content_vbs, f, indent=4)
        print(f"  [+] Simple VBS: dms:{id_dest}") # Simple block state

def step_3_migrate_logic(island_data):
    print(f"\n--- Step 3: Migrating '{FIRM_ISLAND}' ---")
    
    modes = island_data.get("modes", [])
    if not modes:
        print("No 'modes' found.")
        return
        
    id_catharsis_island = modes[0] 
    replacements = island_data.get("replacements", {})
    
    vbs_route = DIR_DESTINY / "assets" / "dms" / "catharsis" / "virtual_block_states"
    vbs_route.mkdir(parents=True, exist_ok=True)
    
    for original_block, destination_block in replacements.items():
        ns_orig, id_orig = original_block.split(":")
        ns_dest, id_dest = destination_block.split(":")
        
        process_virtual_block_state(ns_dest, id_dest, vbs_route)

        # Create replacement for target island
        replace_route = DIR_DESTINY / CATHA_ISLAND / "assets" / CATHA_ISLAND / "catharsis" / "block_replacements" / ns_orig
        replace_route.mkdir(parents=True, exist_ok=True)
        
        replace_file = replace_route / f"{id_orig}.json"
        content_repl = {
            "type": "conditional",
            "condition": {
                "type": "in_island",
                "island": id_catharsis_island
            },
            "definition": {
                "type": "redirect",
                "virtual_state": f"dms:{id_dest}"
            }
        }
        
        with open(replace_file, 'w', encoding='utf-8') as f:
            json.dump(content_repl, f, indent=4)

if __name__ == "__main__":
    print(f"Target island: {FIRM_ISLAND}")
    
    target_file = DIR_ORIGIN / "firmskyblock" / "overrides" / "blocks" / f"{FIRM_ISLAND}.json"
    
    if not target_file.exists():
        print(f"¡ERROR! Couldn't find: {target_file}")
    else:
        keywords, island_data = generate_island_keywords(target_file)
        
        step_1_and_2_copy_only_necessary(keywords)
        step_3_migrate_logic(island_data)