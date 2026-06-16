# Procedures and resources

Beyond conversational memory, Tessera stores reusable how-tos (procedures) and captioned blobs
(resources).

## Procedures

A procedure is a reusable lesson: a `trigger` (the situation), `steps` (what to do), and `success`
(the good outcome). Store one:

```python
proc = client.procedures.remember(
    trigger="installing dependencies in this repo",
    steps=["use uv, not pip", "run `uv sync`"],
    success="deps resolve and CI passes",
    user_id="repo:my-app",
)
```

Recall the ones whose trigger best matches a task. This is a read — it doesn't change use counts:

```python
hits = client.procedures.recall(task="how do I install deps here?", user_id="repo:my-app")
for h in hits.results:
    print(h.procedure.trigger, h.similarity)
    print(h.procedure.steps)
```

Tune recall with `k` (how many) and `min_similarity` (a floor on match quality).

Record how a procedure worked out to reinforce it. A failure still counts as a use:

```python
client.procedures.record_outcome("ep_...", success=True, user_id="repo:my-app")
```

## Resources

A resource is a stored blob handle (e.g. an image) with a caption, recalled by caption or visual
content. Store a handle with a caption you supply, or with an `image_url` for the server to
caption with a VLM:

```python
res = client.resources.remember(
    blob_ref="s3://bucket/diagram.png",
    mime="image/png",
    caption="System architecture: API gateway in front of three services.",
    user_id="repo:my-app",
)
```

Upload a local image to be captioned and embedded (multipart). Only
`.png/.jpg/.jpeg/.gif/.webp` are accepted:

```python
res = client.resources.file(
    path="diagram.png",
    blob_ref="s3://bucket/diagram.png",
    user_id="repo:my-app",
)
```

Recall resources by what they depict:

```python
hits = client.resources.recall(query="architecture diagram", user_id="repo:my-app")
for h in hits.results:
    print(h.resource.caption, h.similarity)
```
