import graphene
from graphene_django import DjangoObjectType
from .models import Note

class NoteType(DjangoObjectType):
    class Meta:
        model = Note
        fields = ('id','title','text','original_language','translated_text','translated_language','translations_count','created_at')

class Query(graphene.ObjectType):
    all_notes = graphene.List(NoteType)
    note = graphene.Field(NoteType, id=graphene.Int(required=True))

    def resolve_all_notes(root, info):
        return Note.objects.all().order_by('-created_at')

    def resolve_note(root, info, id):
        try:
            return Note.objects.get(pk=id)
        except Note.DoesNotExist:
            return None

class TranslateNote(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)
        target = graphene.String(required=True)

    ok = graphene.Boolean()
    original = graphene.String()
    translated = graphene.String()

    def mutate(root, info, id, target):
        try:
            note = Note.objects.get(pk=id)
        except Note.DoesNotExist:
            return TranslateNote(ok=False, original=None, translated=None)
        # synchronous translation for demo
        from .views import translate_text_via_api
        translated = translate_text_via_api(note.text, source=note.original_language or 'auto', target=target)
        if translated:
            note.translated_text = translated
            note.translated_language = target
            note.translations_count = (note.translations_count or 0) + 1
            note.save()
            return TranslateNote(ok=True, original=note.text, translated=translated)
        return TranslateNote(ok=False, original=note.text, translated=None)

class Mutation(graphene.ObjectType):
    translate_note = TranslateNote.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)
