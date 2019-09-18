from django.shortcuts import render, get_object_or_404, reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic import TemplateView
from django.urls import reverse
from .models import Player, Difficulty, Goal, Quiz, QuizData
from random import shuffle
from .utility import ConversionTableResolver


class GoGoal(TemplateView):
    template_name = "treasure/go-goal.html"

    def get(self, request, *args, **kwargs):
        player = get_object_or_404(Player, pk=request.session.get('player_pk'))
        diff_pk = player.difficulty.pk
        kwargs['diff_pk'] = diff_pk
        if(diff_pk == 1):
            kwargs['goal'] = player.difficulty.goal.name
        else:
            kwargs['quizzes'] = player.quizzes.all()
            kwargs['change'] = ('10' if (diff_pk == 2) else '16') + '進数'
            table = ConversionTableResolver.createTable(diff_pk)
            kwargs['corresponds'] = table.data
        return super().get(request, *args, **kwargs)


class Hints(TemplateView):
    template_name = 'treasure/hints.html'

    def get(self, request, *args, **kwargs):
        # セッションからplayerの情報を取得
        player = get_object_or_404(Player,
                                   pk=request.session.get('player_pk', -1))
        # 簡略化
        # hint = {1: player.quiz1.hint, 2: player.quiz2.hint,
        #        3: player.quiz3.hint, 4: player.quiz4.hint}
        # 現在のページに対応したヒントを送信
        # kwargs['hint'] = hint[kwargs['hint_index']]
        quiz_data = player.quizzes.get(order=kwargs['hint_index'] - 1)
        kwargs['hint'] = quiz_data.quiz.hint
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        # キーワードを受け取ったなら
        if self.request.POST.get('number', None):
            # セッションからplayerの情報を取得
            player = get_object_or_404(Player,
                                       pk=request.session.get('player_pk', -1))
            # 簡略化
            # keyword = {1: player.quiz1.keyword, 2: player.quiz2.keyword,
            #           3: player.quiz3.keyword, 4: player.quiz4.keyword}
            # 受け取ったキーワードが現在のページの答えと等しいなら
            quiz_data = player.quizzes.get(order=kwargs['hint_index'] - 1)
            keyword = quiz_data.quiz.keyword
            if keyword == self.request.POST.get('number', None):
                # 正解と送信
                # kwargs['result'] = '正解'
                # 現在が４ページ目なら
                if kwargs['hint_index'] == 4:
                    player.progress = 5
                    # ゴール誘導ページへ
                    return HttpResponseRedirect(reverse('treasure:go-goal'))
                else:
                    player.progress = kwargs['hint_index'] + 1
                    # 次のページへ
                    return HttpResponseRedirect(reverse(
                            'treasure:hints', args=(kwargs['hint_index']+1,)))
            else:
                # 不正解と送信
                kwargs['result'] = '不正解'
        return self.get(request, *args, **kwargs)


class Opening(TemplateView):
    template_name = 'treasure/opening.html'

    def post(self, request, **kwargs):
        if(request.session.get('player_pk', -1) != -1):
            return HttpResponseRedirect(
                reverse('treasure:hints', args=(1,)))
        else:
            return HttpResponseRedirect(reverse('treasure:dif-sel'))


class DifSel(TemplateView):
    template_name = 'treasure/dif-sel.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['difficulties'] = Difficulty.objects.all()
        return context

    def post(self, request, **kwargs):
        dif_pk = request.POST.get('diff', -1)
        difficulty = get_object_or_404(Difficulty, pk=dif_pk)

        quizzes = list(difficulty.quizzes.all())
        shuffle(quizzes)
        # プレイヤー作成
        player = Player.objects.create(difficulty=difficulty, progress=1)
        for i in range(len(quizzes)):
            player.quizzes.add(
                QuizData.objects.create(quiz=quizzes[i], order=i)
            )
        request.session['player_pk'] = player.pk
        return HttpResponseRedirect(reverse('treasure:hints', args=(1,)))


class OnGoal(TemplateView):
    template_name = 'treasure/on-goal.html'

    def get(self, request, **kwargs):
        player = get_object_or_404(Player,
                                   pk=request.session.get('player_pk', -1))
        if kwargs['pk'] == player.difficulty.pk:
            player.progress = 6
            return HttpResponseRedirect(reverse('treasure:last'))
        return super().get(request, **kwargs)


class Last(TemplateView):
    template_name = 'treasure/last.html'

    def get(self, request, **kwargs):
        player = get_object_or_404(Player,
                                   pk=request.session.get('player_pk', -1))
        kwargs['dif'] = player.difficulty
        return super().get(request, **kwargs)