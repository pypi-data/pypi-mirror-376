import os
import ast
import argparse
import importlib.util
from sentence_transformers import SentenceTransformer
import chromadb
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn


# -----------------------------
# Extract functions & methods
# -----------------------------
def extract_functions_from_file(filepath):
    """Extract classes and functions (with docstrings) from a Python file."""
    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()

    tree = ast.parse(source, filename=filepath)
    docs = {}

    for node in ast.walk(tree):
        # Top-level functions
        if isinstance(node, ast.FunctionDef):
            name = node.name
            doc = ast.get_docstring(node) or ""
            key = f"{os.path.basename(filepath)}::{name}"
            docs[key] = f"Function: {name}\nDocstring: {doc}"

        # Class methods
        if isinstance(node, ast.ClassDef):
            class_name = node.name
            for subnode in node.body:
                if isinstance(subnode, ast.FunctionDef):
                    method_name = subnode.name
                    doc = ast.get_docstring(subnode) or ""
                    key = f"{os.path.basename(filepath)}::{class_name}.{method_name}"
                    docs[key] = f"Class: {class_name}\nMethod: {method_name}\nDocstring: {doc}"
    return docs


def _walk_py_files(base_path):
    """Recursively find .py files in base_path."""
    for root, _, files in os.walk(base_path):
        for file in files:
            if file.endswith(".py"):
                yield os.path.join(root, file)


def extract_all_functions(target: str):
    """Extract functions from a local path or a Python module."""
    docs = {}

    if os.path.exists(target):  # local path
        if os.path.isfile(target) and target.endswith(".py"):
            docs.update(extract_functions_from_file(target))
        else:
            for filepath in _walk_py_files(target):
                docs.update(extract_functions_from_file(filepath))
    else:  # assume module
        spec = importlib.util.find_spec(target)
        if not spec:
            raise ValueError(f"Module '{target}' not found")

        if spec.origin.endswith("__init__.py"):  # package
            base_path = os.path.dirname(spec.origin)
        else:  # single file module
            base_path = spec.origin

        if os.path.isdir(base_path):
            for filepath in _walk_py_files(base_path):
                docs.update(extract_functions_from_file(filepath))
        else:
            docs.update(extract_functions_from_file(base_path))

    return docs


# -----------------------------
# Build vector index
# -----------------------------
def build_index(docs):
    chroma_client = chromadb.Client()
    collection = chroma_client.create_collection("codebase")

    model = SentenceTransformer("all-MiniLM-L6-v2")

    for i, (key, text) in enumerate(docs.items()):
        embedding = model.encode([text])[0].tolist()
        collection.add(documents=[text], embeddings=[embedding], ids=[str(i)], metadatas=[{"key": key}])

    return collection, model


def ask(query: str, collection, model, top_k=3):
    query_emb = model.encode([query])[0].tolist()
    results = collection.query(query_embeddings=[query_emb], n_results=top_k)

    answers = []
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        answers.append({
            "key": meta["key"],
            "text": doc
        })
    return answers


# -----------------------------
# Webserver
# -----------------------------
def create_app(collection, model):
    app = FastAPI()

    @app.get("/", response_class=HTMLResponse)
    async def index():
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>PyBenChatBot</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                #chat { border: 1px solid #ccc; padding: 10px; height: 400px; overflow-y: scroll; }
                .msg { margin: 5px 0; }
                .user { color: blue; }
                .bot { color: green; white-space: pre-wrap; } /* preserve line breaks */
                footer { margin-top: 20px; font-size: 14px; color: #555; text-align: right;}
            </style>

        </head>
        <body>
            <h2>Chat with Your Codebase 🤖</h2>
            <div id="chat"></div>
            <input type="text" id="input" placeholder="Ask something..." style="width: 80%;">
            <button onclick="send()">Send</button>

            <footer>
                Powered by Ben Moskovitch at 
                <a href="https://github.com/DarkFlameBEN/PyBenChatBot" target="_blank">PyBenChatBot</a>
            </footer>

            <script>
                let history = [];
                let historyIndex = -1;

                async function send() {
                    let input = document.getElementById("input");
                    let msg = input.value;
                    if (!msg) return;
                    let chat = document.getElementById("chat");

                    chat.innerHTML += "<div class='msg user'><b>You:</b> " + msg + "</div>";

                    // Save to history
                    history.unshift(msg);
                    if (history.length > 10) history.pop();
                    historyIndex = -1;

                    input.value = "";

                    let resp = await fetch("/ask", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({query: msg})
                    });
                    let data = await resp.json();

                    // ✅ Show all results with key/module info
                    let answers = data.answers;
                    answers.forEach((ans, idx) => {
                        chat.innerHTML += "<div class='msg bot'><b>Bot (result " + (idx+1) + " from " + ans.key + "):</b><br>" + ans.text + "</div>";
                    });

                    chat.scrollTop = chat.scrollHeight;
                }

                // 🔑 Add Enter + Arrow key support
                document.getElementById("input").addEventListener("keydown", function(event) {
                    if (event.key === "Enter") {
                        event.preventDefault();
                        send();
                    } else if (event.key === "ArrowUp") {
                        if (history.length > 0) {
                            if (historyIndex < history.length - 1) historyIndex++;
                            document.getElementById("input").value = history[historyIndex];
                        }
                        event.preventDefault();
                    } else if (event.key === "ArrowDown") {
                        if (historyIndex > 0) {
                            historyIndex--;
                            document.getElementById("input").value = history[historyIndex];
                        } else {
                            historyIndex = -1;
                            document.getElementById("input").value = "";
                        }
                        event.preventDefault();
                    }
                });
            </script>
        </body>
        </html>
        """

    @app.post("/ask")
    async def ask_api(request: Request):
        data = await request.json()
        query = data.get("query", "")
        answers = ask(query, collection, model, top_k=3)
        return JSONResponse({"answers": answers})

    return app


def main():
    """Runs a local PyBenChatBot webserver"""
    parser = argparse.ArgumentParser(description="Runs a local PyBenChatBot webserver")
    parser.add_argument('-t', "--target", type=str, default=".", help="Path or Python module to index",
                        required=False)
    parser.add_argument('-p', "--port", type=int, default=8000, help="Webserver port (default: 8000)",
                        required=False)
    args = parser.parse_args()

    print(f"🔍 Indexing {args.target} ...")
    docs = extract_all_functions(args.target)
    print(f"Indexed {len(docs)} functions/methods")

    collection, model = build_index(docs)

    app = create_app(collection, model)

    print(f"🚀 Starting server at http://127.0.0.1:{args.port}")
    uvicorn.run(app, host="127.0.0.1", port=args.port)

if __name__ == "__main__":
    main()