import argparse, hashlib, json, os, shutil, subprocess, sys, time
import msvcrt
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
from urllib.request import urlopen, Request
from PIL import Image, ImageDraw, ImageFont

BASE = Path(r"E:\HealingMart-Stock")
CFG = json.loads((BASE / "stock-config.json").read_text(encoding="utf-8"))
UPLOAD = Path(CFG["upload_dir"])
DONE = Path(CFG["done_dir"])
ERROR = Path(CFG["error_dir"])
META = Path(CFG["meta_dir"])
THUMBS = Path(CFG["thumbs_dir"])
REPO = Path(CFG["repo_dir"])
ASSET_ROOT = Path(CFG["asset_root"])
MANIFEST = REPO / CFG["manifest_path"]
MANIFEST_JS = REPO / CFG["manifest_js_path"]
CATEGORIES = REPO / "stock" / "categories.json"
CATEGORIES_JS = REPO / "stock" / "categories.js"
LOG = BASE / "LOGS" / "uploader.log"
IMAGE_EXTS = {x.lower() for x in CFG["image_extensions"]}
VIDEO_EXTS = {x.lower() for x in CFG["video_extensions"]}
BRANCH = CFG.get("repo_branch", "main")
PUBLIC_BASE = CFG["public_base"].rstrip("/") + "/"
SCAN_SECONDS = int(CFG.get("scan_seconds", 5))
STATE_FILE = BASE / "processed-state.json"
SEQ_FILE = BASE / "sequence-counters.json"
LOGO_FILE = REPO / "healingmart_logo_transparent_90.webp"
PREVIEW_MAX = 1280
THUMB_MAX = 640

def load_state():
    try:
        d=json.loads(STATE_FILE.read_text(encoding="utf-8"))
        return d if isinstance(d,dict) else {}
    except Exception:
        return {}

def write_state(state):
    STATE_FILE.write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding="utf-8")

def state_key(path):
    return path.relative_to(UPLOAD).as_posix()

def stat_fingerprint(path):
    st=path.stat()
    return {"size":st.st_size,"mtime_ns":st.st_mtime_ns}

def unchanged_in_state(path,state):
    rec=state.get(state_key(path))
    if not isinstance(rec,dict): return False
    try:
        fp=stat_fingerprint(path)
        return rec.get("size")==fp["size"] and rec.get("mtime_ns")==fp["mtime_ns"]
    except OSError:
        return False

def mark_state(path,state,digest=None,status="processed"):
    fp=stat_fingerprint(path)
    state[state_key(path)]={"size":fp["size"],"mtime_ns":fp["mtime_ns"],"sha256":digest,"status":status,"at":datetime.now(timezone.utc).isoformat()}

def load_sequences():
    try:
        d=json.loads(SEQ_FILE.read_text(encoding="utf-8"))
        return d if isinstance(d,dict) else {}
    except Exception:
        return {}

def write_sequences(d):
    SEQ_FILE.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding="utf-8")

def category_key(cats):
    return "/".join(cats)

def next_sequence(cats, seqs, items):
    key=category_key(cats)
    current=int(seqs.get(key,0) or 0)
    seen=[int(x.get("sequence") or 0) for x in items if x.get("categories")==cats]
    n=max([current]+seen+[0])+1
    seqs[key]=n
    return n

def public_stem(cats, seq):
    leaf=safe_segment(cats[-1]).replace(" ","-")
    return f"{leaf}-{seq:03d}"

def display_title(cats, seq):
    return f"{cats[-1]} 이미지 {seq:03d}"

def has_alpha(im):
    if "A" in im.getbands():
        lo,hi=im.getchannel("A").getextrema()
        return lo < 255
    return im.mode=="P" and "transparency" in im.info

def fit_copy(im, max_edge):
    out=im.copy()
    out.thumbnail((max_edge,max_edge),Image.Resampling.LANCZOS)
    return out

def apply_logo(im):
    # Preview/thumbnail watermark: centered text only.
    # The clean full-resolution download remains untouched.
    base=im.convert("RGBA")
    text="HealingMart Stock"
    draw=ImageDraw.Draw(base)
    font_path=Path(r"C:\Windows\Fonts\seguisb.ttf")
    fallback=Path(r"C:\Windows\Fonts\arialbd.ttf")
    font_file=font_path if font_path.exists() else fallback
    target_w=max(180,int(base.width*0.42))
    size=max(18,int(base.width*0.07))
    font=None
    while size>=12:
        try:
            font=ImageFont.truetype(str(font_file),size)
        except Exception:
            font=ImageFont.load_default()
        box=draw.textbbox((0,0),text,font=font,stroke_width=max(1,size//24))
        if box[2]-box[0] <= target_w:
            break
        size-=2
    box=draw.textbbox((0,0),text,font=font,stroke_width=max(1,size//24))
    tw,th=box[2]-box[0],box[3]-box[1]
    x=(base.width-tw)//2
    y=(base.height-th)//2-box[1]
    stroke=max(1,size//24)
    # Soft dark underlay plus translucent white lettering keeps the mark legible
    # on both light and dark stock while remaining obviously a preview watermark.
    draw.text((x+2,y+2),text,font=font,fill=(0,0,0,95),stroke_width=stroke,stroke_fill=(0,0,0,110))
    draw.text((x,y),text,font=font,fill=(255,255,255,105),stroke_width=stroke,stroke_fill=(255,255,255,45))
    return base

def save_webp(im, path, transparent, preview=False):
    path.parent.mkdir(parents=True,exist_ok=True)
    if transparent:
        out=im.convert("RGBA")
        out.save(path,"WEBP",lossless=True,method=6)
    else:
        out=im.convert("RGB")
        out.save(path,"WEBP",quality=88 if preview else 92,method=6)

def create_asset_set(src, cats, seq):
    stem=public_stem(cats,seq)
    full_rel=ASSET_ROOT.joinpath(*cats,"full",stem+".webp")
    preview_rel=ASSET_ROOT.joinpath(*cats,"preview",stem+".webp")
    thumb_rel=ASSET_ROOT.joinpath(*cats,"thumb",stem+".webp")
    with Image.open(src) as im0:
        im=im0.convert("RGBA") if (has_alpha(im0) or im0.mode in ("RGBA","LA","P")) else im0.convert("RGB")
        transparent=has_alpha(im)
        width,height=im.size
        save_webp(im,REPO/full_rel,transparent,preview=False)
        prev=apply_logo(fit_copy(im,PREVIEW_MAX))
        save_webp(prev,REPO/preview_rel,True,preview=True)
        th=apply_logo(fit_copy(im,THUMB_MAX))
        save_webp(th,REPO/thumb_rel,True,preview=True)
    return {
        "stem":stem,"full_rel":full_rel,"preview_rel":preview_rel,"thumb_rel":thumb_rel,
        "width":width,"height":height,"transparent":transparent
    }

def remove_item_assets(item):
    rels=[item.get("repo_path"),item.get("preview_repo_path"),item.get("thumb_repo_path")]
    for rel in rels:
        if not rel: continue
        p=REPO/rel
        if p.exists():
            p.unlink()

for d in (UPLOAD, DONE, ERROR, META, THUMBS, LOG.parent):
    d.mkdir(parents=True, exist_ok=True)

def log(msg):
    line=f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  {msg}"
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")

def run(cmd, cwd=None, check=True):
    p=subprocess.run(cmd, cwd=str(cwd) if cwd else None, text=True,
                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                     encoding="utf-8", errors="replace")
    if check and p.returncode:
        raise RuntimeError(f"command failed ({p.returncode}): {' '.join(cmd)}\n{p.stdout[-1200:]}")
    return p

def purge_jsdelivr(paths):
    base="https://purge.jsdelivr.net/gh/healingmart/image@main/"
    ok=0
    for rel in paths:
        try:
            req=Request(base+rel,headers={"User-Agent":"HealingMart-Stock-Auto/1.0"})
            with urlopen(req,timeout=15) as r:
                r.read(256)
            ok+=1
        except Exception as e:
            log(f"CDN_PURGE_WARN: {rel} :: {e}")
    if ok:
        log(f"CDN_PURGE_OK: {ok}개")

def sha256(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for chunk in iter(lambda:f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()

def stable(path):
    try:
        a=path.stat()
        time.sleep(1.5)
        b=path.stat()
        return a.st_size==b.st_size and a.st_mtime_ns==b.st_mtime_ns
    except OSError:
        return False

def safe_segment(s):
    s=s.strip().replace("\\","-").replace("/","-")
    bad='<>:"|?*'
    for c in bad: s=s.replace(c,"-")
    return s.strip(" .") or "미분류"

def rel_categories(path):
    rel=path.relative_to(UPLOAD)
    parts=[safe_segment(x) for x in rel.parts[:-1]]
    return parts or ["미분류"]

def image_info(path):
    with Image.open(path) as im:
        width,height=im.size
        fmt=im.format or path.suffix.lstrip(".").upper()
        transparent=False
        if "A" in im.getbands():
            a=im.getchannel("A")
            lo,hi=a.getextrema()
            transparent=lo < 255
        elif im.mode=="P" and "transparency" in im.info:
            transparent=True
        return width,height,fmt,transparent

def load_manifest():
    if not MANIFEST.exists():
        return {"version":1,"updated_at":None,"items":[]}
    try:
        data=json.loads(MANIFEST.read_text(encoding="utf-8"))
        if isinstance(data,list): return {"version":1,"updated_at":None,"items":data}
        data.setdefault("items",[])
        return data
    except Exception:
        return {"version":1,"updated_at":None,"items":[]}

def raw_url(repo_rel):
    return PUBLIC_BASE + "/".join(quote(p) for p in Path(repo_rel).as_posix().split("/"))

def unique_repo_rel(categories, filename):
    folder=ASSET_ROOT.joinpath(*categories)
    candidate=folder / filename
    if not (REPO/candidate).exists():
        return candidate
    stem=Path(filename).stem
    ext=Path(filename).suffix
    return folder / f"{stem}-{datetime.now().strftime('%Y%m%d-%H%M%S')}{ext}"

def move_done(src):
    rel=src.relative_to(UPLOAD)
    dst=DONE/rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        dst=dst.with_name(dst.stem+"-"+datetime.now().strftime("%Y%m%d-%H%M%S")+dst.suffix)
    shutil.move(str(src),str(dst))
    return dst

def move_error(src):
    rel=src.relative_to(UPLOAD)
    dst=ERROR/rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        dst=dst.with_name(dst.stem+"-"+datetime.now().strftime("%Y%m%d-%H%M%S")+dst.suffix)
    shutil.move(str(src),str(dst))
    return dst

CATEGORY_SPECIAL = {"_삭제","_보류","_임시"}

def category_paths_from_folders():
    paths=[]
    for p in UPLOAD.rglob("*"):
        if not p.is_dir():
            continue
        rel=p.relative_to(UPLOAD)
        parts=list(rel.parts)
        if not parts:
            continue
        if any((part in CATEGORY_SPECIAL) or part.startswith("__") for part in parts):
            continue
        parts=[safe_segment(x) for x in parts]
        paths.append("/".join(parts))
    return sorted(set(paths), key=lambda x:(x.count("/"), x.lower()))

def category_tree(paths):
    root={}
    for path in paths:
        node=root
        acc=[]
        for part in path.split("/"):
            acc.append(part)
            if part not in node:
                node[part]={"name":part,"path":"/".join(acc),"children":{}}
            node=node[part]["children"]

    def convert(d):
        return [
            {"name":v["name"],"path":v["path"],"children":convert(v["children"])}
            for _,v in sorted(d.items(), key=lambda kv:kv[0].lower())
        ]
    return convert(root)

def build_category_payload():
    paths=category_paths_from_folders()
    return {
        "version":1,
        "paths":paths,
        "categories":category_tree(paths)
    }

def category_payload_changed(payload):
    try:
        old=json.loads(CATEGORIES.read_text(encoding="utf-8"))
        return old.get("paths",[]) != payload.get("paths",[])
    except Exception:
        return True

def write_categories(payload):
    out=dict(payload)
    out["updated_at"]=datetime.now(timezone.utc).isoformat()
    CATEGORIES.parent.mkdir(parents=True,exist_ok=True)
    CATEGORIES.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
    CATEGORIES_JS.write_text(
        "window.HMSTOCK_REMOTE_CATEGORIES="+json.dumps(out,ensure_ascii=False,separators=(",",":"))+";\n",
        encoding="utf-8"
    )

def write_manifest(data):
    data["updated_at"]=datetime.now(timezone.utc).isoformat()
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
    MANIFEST_JS.write_text(
        "window.HMSTOCK_REMOTE_MANIFEST="+json.dumps(data,ensure_ascii=False,separators=(",",":"))+";\n",
        encoding="utf-8"
    )

def ensure_repo_clean_pull():
    st=run(["git","status","--porcelain"],cwd=REPO).stdout.strip()
    allowed=[]
    if st:
        lines=[x for x in st.splitlines() if not (" stock/" in x or x.endswith(" stock"))]
        if lines:
            raise RuntimeError("image repo has unrelated local changes; aborting safe auto-upload:\n"+"\n".join(lines[:20]))
    run(["git","pull","--ff-only"],cwd=REPO)

def process_batch():
    state=load_state()
    state_dirty=False
    files=sorted([p for p in UPLOAD.rglob("*") if p.is_file()],
                 key=lambda p:p.stat().st_mtime)

    def top_folder(path):
        rel=path.relative_to(UPLOAD)
        return rel.parts[0] if len(rel.parts) > 1 else ""

    category_payload=build_category_payload()
    categories_changed=category_payload_changed(category_payload)

    delete_images=[p for p in files if p.suffix.lower() in IMAGE_EXTS and top_folder(p) == "_삭제" and not unchanged_in_state(p,state)]
    images=[p for p in files if p.suffix.lower() in IMAGE_EXTS and top_folder(p) not in {"_삭제","_보류","_임시"} and not unchanged_in_state(p,state)]
    videos=[p for p in files if p.suffix.lower() in VIDEO_EXTS]
    if videos and not CFG.get("video_enabled",False):
        new_videos=[p for p in videos if not unchanged_in_state(p,state)]
        if new_videos:
            log(f"VIDEO_WAIT: {len(new_videos)}개 새 영상 (영상 자동화는 현재 비활성)")
            for vp in new_videos:
                mark_state(vp,state,status="video_wait")
            state_dirty=True
    ready=[p for p in images if stable(p)]
    delete_ready=[p for p in delete_images if stable(p)]
    if not ready and not delete_ready and not categories_changed:
        if state_dirty: write_state(state)
        return 0

    ensure_repo_clean_pull()

    # pull 이후 한 번 더 폴더 상태를 읽어 실제 현재 구조로 기록
    category_payload=build_category_payload()
    categories_changed=category_payload_changed(category_payload)
    if categories_changed:
        write_categories(category_payload)
        log(f"CATEGORIES_SYNC: {len(category_payload['paths'])}개 폴더 카테고리")

    data=load_manifest()
    items=data["items"]
    seqs=load_sequences()
    seqs_dirty=False
    by_hash={x.get("sha256"):x for x in items if x.get("sha256")}
    completed=[]
    newly_added=[]
    updated_items=[]
    deleted_items=[]

    # _삭제 폴더: 같은 파일 해시의 공개 스톡 항목을 제거
    for src in delete_ready:
        try:
            digest=sha256(src)
            existing=by_hash.get(digest)
            if existing:
                remove_item_assets(existing)
                items.remove(existing)
                by_hash.pop(digest,None)
                deleted_items.append(existing)
                mid=existing.get("id")
                if mid:
                    mp=META/f"{mid}.json"
                    if mp.exists(): mp.unlink()
                log(f"DELETE_PREPARED: {src.name} -> 기존 ID {existing.get('id')}")
            else:
                log(f"DELETE_NOT_FOUND: {src.name}")
            completed.append(src)
            mark_state(src,state,digest,status="deleted" if existing else "delete_not_found")
            state_dirty=True
        except Exception as e:
            log(f"DELETE_ERROR: {src} :: {e}")
            try: move_error(src)
            except Exception: pass

    for src in ready:
        try:
            digest=sha256(src)
            cats=rel_categories(src)
            if digest in by_hash:
                existing=by_hash[digest]
                old_cats=existing.get("categories") or [existing.get("category")]
                old_cats=[x for x in old_cats if x]
                if old_cats == cats:
                    log(f"DUPLICATE: {src.name} -> 기존 ID {existing.get('id')} (원본 유지)")
                    completed.append(src)
                    mark_state(src,state,digest,status="duplicate")
                    state_dirty=True
                    continue

                # 같은 파일을 다른 카테고리 폴더에 다시 넣으면 새 카테고리 규칙으로 자산/번호를 재생성
                remove_item_assets(existing)
                seq=next_sequence(cats,seqs,items)
                seqs_dirty=True
                aset=create_asset_set(src,cats,seq)
                full_rel=aset["full_rel"]; preview_rel=aset["preview_rel"]; thumb_rel=aset["thumb_rel"]
                url=raw_url(full_rel); preview_url=raw_url(preview_rel); thumb_url=raw_url(thumb_rel)
                keep_tags=[t for t in existing.get("tags",[]) if t not in old_cats]
                existing["sequence"]=seq
                existing["title"]=display_title(cats,seq)
                existing["category"]=cats[0]
                existing["categories"]=cats
                existing["tags"]=list(dict.fromkeys(["HM-스톡","이미지"]+cats+[
                    t for t in keep_tags if t not in {"HM-스톡","이미지"}
                ]))
                if aset["transparent"] and "투명" not in existing["tags"]:
                    existing["tags"] += ["투명","누끼"]
                existing["file"]=aset["stem"]+".webp"
                existing["repo_path"]=full_rel.as_posix()
                existing["preview_repo_path"]=preview_rel.as_posix()
                existing["thumb_repo_path"]=thumb_rel.as_posix()
                existing["url"]=preview_url
                existing["preview_url"]=preview_url
                existing["download_url"]=url
                existing["thumb_url"]=thumb_url
                existing["width"]=aset["width"]
                existing["height"]=aset["height"]
                existing["format"]="WEBP"
                existing["transparent"]=aset["transparent"]
                existing["updated_at"]=datetime.now(timezone.utc).isoformat()
                updated_items.append(existing)
                completed.append(src)
                mid=existing.get("id")
                if mid:
                    (META/f"{mid}.json").write_text(json.dumps(existing,ensure_ascii=False,indent=2),encoding="utf-8")
                log(f"RECATEGORIZED: {src.name} {old_cats} -> {cats} / {existing['file']}")
                mark_state(src,state,digest,status="recategorized")
                state_dirty=True
                continue

            seq=next_sequence(cats,seqs,items)
            seqs_dirty=True
            aset=create_asset_set(src,cats,seq)
            item_id=digest[:16]
            full_url=raw_url(aset["full_rel"])
            preview_url=raw_url(aset["preview_rel"])
            thumb_url=raw_url(aset["thumb_rel"])
            tags=["HM-스톡","이미지"]+cats
            if aset["transparent"]:
                tags += ["투명","누끼"]
            item={
                "id":item_id,
                "kind":"image",
                "sequence":seq,
                "title":display_title(cats,seq),
                "category":cats[0],
                "categories":cats,
                "tags":list(dict.fromkeys(tags)),
                "file":aset["stem"]+".webp",
                "original_name":src.name,
                "repo_path":aset["full_rel"].as_posix(),
                "preview_repo_path":aset["preview_rel"].as_posix(),
                "thumb_repo_path":aset["thumb_rel"].as_posix(),
                "url":preview_url,
                "preview_url":preview_url,
                "download_url":full_url,
                "thumb_url":thumb_url,
                "width":aset["width"],
                "height":aset["height"],
                "format":"WEBP",
                "transparent":aset["transparent"],
                "source_size_bytes":src.stat().st_size,
                "size_bytes":(REPO/aset["full_rel"]).stat().st_size,
                "sha256":digest,
                "added_at":datetime.now(timezone.utc).isoformat(),
                "source":"github",
                "license":"HealingMart Stock License"
            }
            items.insert(0,item)
            by_hash[digest]=item
            newly_added.append(item)
            completed.append(src)
            (META/f"{item_id}.json").write_text(json.dumps(item,ensure_ascii=False,indent=2),encoding="utf-8")
            log(f"PREPARED: {src.name} -> {item['file']} [{category_key(cats)}] {aset['width']}x{aset['height']} transparent={aset['transparent']}")
            mark_state(src,state,digest,status="uploaded")
            state_dirty=True
        except Exception as e:
            log(f"FILE_ERROR: {src} :: {e}")
            try: move_error(src)
            except Exception: pass

    changed_count=len(newly_added)+len(updated_items)+len(deleted_items)
    if changed_count:
        write_manifest(data)

    if changed_count or categories_changed:
        run([
            "git","add","-A",
            ASSET_ROOT.as_posix(),
            CFG["manifest_path"],CFG["manifest_js_path"],
            "stock/categories.json","stock/categories.js"
        ],cwd=REPO)
        msg=f"Update HealingMart Stock (+{len(newly_added)} ~{len(updated_items)} -{len(deleted_items)} cat={'1' if categories_changed else '0'})"
        c=run(["git","commit","-m",msg],cwd=REPO,check=False)
        if c.returncode not in (0,1):
            raise RuntimeError(c.stdout)
        run(["git","push","origin",BRANCH],cwd=REPO)
        log(f"GITHUB_PUSH_OK: +{len(newly_added)} ~{len(updated_items)} -{len(deleted_items)} category_sync={categories_changed}")
        purge_targets=[]
        if changed_count:
            purge_targets += ["stock/manifest.json","stock/manifest.js"]
        if categories_changed:
            purge_targets += ["stock/categories.json","stock/categories.js"]
        if purge_targets:
            # GitHub raw/content propagation can lag a few seconds immediately after push.
            # Purging jsDelivr too early may repopulate the CDN with the previous manifest,
            # so wait briefly and purge twice for reliable folder/image visibility.
            time.sleep(3.0)
            purge_jsdelivr(purge_targets)
            time.sleep(2.0)
            purge_jsdelivr(purge_targets)

    if seqs_dirty:
        write_sequences(seqs)
    if state_dirty:
        write_state(state)
    for src in completed:
        if src.exists():
            log(f"KEPT: {src} (UPLOAD 원본 유지)")
    return len(newly_added)+len(updated_items)+len(deleted_items)

def acquire_watch_lock():
    lock_path = BASE / "stock-auto.lock"
    fh = open(lock_path, "a+b")
    fh.seek(0, os.SEEK_END)
    if fh.tell() == 0:
        fh.write(b"0")
        fh.flush()
    fh.seek(0)
    try:
        msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError:
        fh.close()
        return None
    return fh

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--watch",action="store_true")
    ap.add_argument("--once",action="store_true")
    args=ap.parse_args()
    watch_lock = None
    if args.watch:
        watch_lock = acquire_watch_lock()
        if watch_lock is None:
            log("WATCH_ALREADY_RUNNING: duplicate watcher blocked.")
            return
    log("HealingMart Stock image automation started.")
    if args.watch:
        while True:
            try: process_batch()
            except Exception as e: log("BATCH_ERROR: "+str(e))
            time.sleep(SCAN_SECONDS)
    else:
        n=process_batch()
        log(f"ONE_SHOT_DONE: {n} new image(s)")

if __name__=="__main__":
    main()
