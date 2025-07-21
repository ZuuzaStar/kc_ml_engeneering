'''
In this python method we explain work of several db endpoints, that will help to get info we need.
We use Post, User and Feed classes as db schemas and ...Get classes as requested data templates and response models.
'''

from fastapi import FastAPI, HTTPException, Depends, Query
from table_feed import Post, User, Feed
from schema import UserGet, PostGet, FeedGet
from database import SessionLocal
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

app = FastAPI()


# Database connect session
def get_db():
    db = SessionLocal()
    try:
        # Return generator with dependency injection
        yield db
    finally:
        # This part at least will be started anyway
        db.close()

####----------------####
#### Post endpoints ####
####----------------#### 

# Enpoint for getting post info by id
@app.get("/post/{id}", response_model=PostGet)
def get_post(
    id: int,
    db: Session = Depends(get_db)
):
    result = db \
    .query(Post) \
    .filter(Post.id == id) \
    .first()

    # For case when there is no requested id in db
    if not result:
        raise HTTPException(404, detail="post not found")
    return PostGet(
        id=result.id,
        text=result.text,
        topic=result.topic
    )

# Endpoint for getting feed info by post id
@app.get("/post/{id}/feed", response_model=List[FeedGet])
def get_post_feed(
    id: int, 
    limit: int = Query(10, description="Limit for rows output"), 
    db: Session = Depends(get_db)
):
    # We need to return empty list if there is no such id in db
    result = db \
    .query(Feed) \
    .filter(Feed.post_id == id) \
    .order_by(Feed.time.desc()) \
    .limit(limit) \
    .all()

    return result

####----------------####
#### User endpoints ####
####----------------####

# Enpoint for getting user info by id
@app.get("/user/{id}", response_model=UserGet)
def get_user(
    id: int,
    db: Session = Depends(get_db)
):
    result = db \
    .query(User) \
    .filter(User.id == id) \
    .first()

    # For case when there is no requested id in db
    if not result:
        raise HTTPException(404, detail="user not found")
    return UserGet(
        age = result.age,
        city = result.city,
        country = result.country,
        exp_group = result.exp_group,
        gender = result.gender,
        id = result.id,
        os = result.os,
        source = result.source
    )

# Endpoint for getting feed info by user id
@app.get("/user/{id}/feed", response_model=List[FeedGet])
def get_post_feed(
    id: int, 
    limit: int = Query(10, description="Limit for rows output"), 
    db: Session = Depends(get_db)
):
    # We need to return empty list if there is no such id in db
    result = db \
    .query(Feed) \
    .filter(Feed.user_id == id) \
    .order_by(Feed.time.desc()) \
    .limit(limit) \
    .all()

    return result

####---------------------------------####
#### Final project endpoint part 1/4 ####
####---------------------------------#### 
@app.get("/post/recommendations/", response_model=List[PostGet])
def get_recommendations(
    id: int = Query(0, description="Input query param with user id (not using)"), 
    limit: int = Query(10, description="Limit for rows output"),
    db: Session = Depends(get_db)
):
    # Get top posts with likes
    result = db \
    .query(Post.id, Post.text, Post.topic, func.count(Feed.post_id).label("likes_count")) \
    .join(Feed, Feed.post_id == Post.id) \
    .filter(Feed.action == "like") \
    .group_by(Post.id, Post.text, Post.topic) \
    .order_by(func.count(Feed.post_id).desc()) \
    .limit(limit) \
    .all()

    return [
        PostGet(
            id=post.id,
            text=post.text,
            topic=post.topic
        ) for post in result
    ]
