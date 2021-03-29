import logging
from django.views.generic import TemplateView, DetailView, UpdateView
from django.core.exceptions import ObjectDoesNotExist
from flaim.database.models import Product, ProductImage, \
    LoblawsProduct, WalmartProduct, VoilaProduct, GroceryGatewayProduct, \
    NutritionFacts
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect

logger = logging.getLogger(__name__)


# Create your views here.
class IndexView(LoginRequiredMixin, TemplateView):
    template_name = 'product_browser/index.html'


def get_product_history_diff(obj):
    """ Get diff list for the history of a given object e.g. Product, LoblawsProduct or NutritionFacts """
    history = obj.history.all()
    new_record = history.first()
    old_record = history.first().prev_record
    delta = new_record.diff_against(old_record)
    if len(delta.changes) > 0:
        return delta.changes
    return None


class ProductView(LoginRequiredMixin, DetailView):
    model = Product
    template_name = 'product_browser/detail.html'
    context_object_name = 'product'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        images = ProductImage.objects.filter(product__product_code=context['product'].product_code)
        images_formatted = [i.image_path.url for i in images]
        context['product_images'] = images_formatted

        # History
        # https://django-simple-history.readthedocs.io/en/latest/history_diffing.html
        context['product_changes'] = get_product_history_diff(context['product'])
        if context['product'].store == 'LOBLAWS':
            context['store_changes'] = get_product_history_diff(LoblawsProduct.objects.get(product=context['product']))
        elif context['product'].store == 'WALMART':
            context['store_changes'] = get_product_history_diff(WalmartProduct.objects.get(product=context['product']))
        elif context['product'].store == 'VOILA':
            context['store_changes'] = get_product_history_diff(VoilaProduct.objects.get(product=context['product']))
        elif context['product'].store == 'GROCERYGATEWAY':
            context['store_changes'] = get_product_history_diff(
                GroceryGatewayProduct.objects.get(product=context['product']))

        try:
            context['nutrition_changes'] = get_product_history_diff(
                NutritionFacts.objects.get(product=context['product']))
        except ObjectDoesNotExist as e:
            context['nutrition_changes'] = None

        # TODO: Move this styling junk somewhere else
        # Predicted category styling
        if context['product'].category.predicted_category_1 is not None:
            if context['product'].category.confidence_1 > 0.90:
                context['confidence_styling'] = 'text-success'
            elif context['product'].category.confidence_1 > 0.50:
                context['confidence_styling'] = 'text-warning'
            elif context['product'].category.confidence_1 < 0.50:
                context['confidence_styling'] = 'text-danger'

        # Predicted subcategory
        if context['product'].subcategory.predicted_subcategory_1 is not None:
            if context['product'].subcategory.confidence_1 > 0.90:
                context['subcategory_confidence_styling'] = 'text-success'
            elif context['product'].subcategory.confidence_1 > 0.50:
                context['subcategory_confidence_styling'] = 'text-warning'
            elif context['product'].subcategory.confidence_1 < 0.50:
                context['subcategory_confidence_styling'] = 'text-danger'

        return context

# class to Update the details in Product_browser/detail
class ProductUpdateView(LoginRequiredMixin, UpdateView):
    model = Product
    fields = ('name', 'brand')
    template_name = 'product_browser/product_form.html'

    def form_valid(self, form):
        updatdeForm = form.save()
        return redirect('product_browser:product_view', pk=updatdeForm.pk)
