from django.shortcuts import render
from django.views.generic import CreateView
from .models import Conductor
from .forms import ConductorForm
from django.http import JsonResponse

class ConductorCreateView(CreateView):
    model = Conductor
    form_class = ConductorForm
    template_name = 'gestion_taller/conductor_form.html'
    
    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return render(request, 'gestion_taller/conductor_form_ajax.html', {'form': self.get_form()})
        return super().get(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            form = self.get_form()
            if form.is_valid():
                self.object = form.save()
                return JsonResponse({'success': True})
            return JsonResponse({'success': False, 'errors': form.errors})
        return super().post(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('conductores')
