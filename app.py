import uuid
from sanic import Sanic, json
from sanic.exceptions import NotFound, BadRequest
from pydantic import BaseModel, ValidationError
from typing import Optional

app = Sanic("PeopleAPI")

# In-memory store
people: dict[str, dict] = {}


# --- Pydantic Models ---

class Address(BaseModel):
    street: str
    house_number: str
    city: str
    country: str
    zip_code: str
    entrance: Optional[str] = None
    floor: Optional[int] = None
    apartment: Optional[str] = None


class AddressUpdate(BaseModel):
    street: Optional[str] = None
    house_number: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    zip_code: Optional[str] = None
    entrance: Optional[str] = None
    floor: Optional[int] = None
    apartment: Optional[str] = None


class PersonCreate(BaseModel):
    name: str
    email: str
    age: Optional[int] = None
    address: Optional[Address] = None


class PersonUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    age: Optional[int] = None
    address: Optional[AddressUpdate] = None


# --- Helper ---

def parse_body(request, model):
    try:
        return model.model_validate(request.json or {})
    except ValidationError as e:
        raise BadRequest(str(e))


# --- Routes ---

@app.get("/people")
async def get_all(request):
    return json(list(people.values()))


@app.post("/people")
async def create_person(request):
    data = parse_body(request, PersonCreate)
    person_id = str(uuid.uuid4())
    person = {"id": person_id, **data.model_dump()}
    people[person_id] = person
    return json(person, status=201)


@app.get("/people/<person_id:str>")
async def get_one(request, person_id: str):
    if person_id not in people:
        raise NotFound(f"Person '{person_id}' not found")
    return json(people[person_id])


@app.put("/people/<person_id:str>")
async def update_person(request, person_id: str):
    if person_id not in people:
        raise NotFound(f"Person '{person_id}' not found")
    data = parse_body(request, PersonUpdate)
    person = people[person_id]
    updates = data.model_dump(exclude_none=True)
    if "address" in updates and person.get("address"):
        person["address"].update(updates.pop("address"))
    elif "address" in updates:
        person["address"] = updates.pop("address")
    person.update(updates)
    return json(person)


@app.delete("/people/<person_id:str>")
async def delete_one(request, person_id: str):
    if person_id not in people:
        raise NotFound(f"Person '{person_id}' not found")
    del people[person_id]
    return json({"message": f"Person '{person_id}' deleted"})


@app.delete("/people")
async def delete_all(request):
    people.clear()
    return json({"message": "All people deleted"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
