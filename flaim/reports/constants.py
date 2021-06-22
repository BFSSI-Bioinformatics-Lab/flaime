FREE_SUGARS = {
    'Sugar-based Ingredients': [
        'barbados sugar',
        'muscovado',
        'barley malt',
        'beet sugar',
        'burnt sugar',
        'caramelized sugar',
        'cane juice',
        'cane juice crystals',
        'cane sugar',
        'castor sugar',
        'caster sugar',
        'coarse sugar',
        'coconut palm sugar',
        'coconut sugar',
        'crystalline fructose',
        'date sugar',
        'dehydrated cane juice',
        'demerara-style sugar',
        'evaporated cane juice',
        'evaporated cane sugar',
        'dried cane syrup',
        'cane syrup solids',
        'fondant sugar',
        'free-flowing brown sugars',
        'fructose',
        'fructose solids',
        'fructose syrup',
        'fruit sugar',
        'galactose',
        'glucose-fructose',
        'granulated sugar',
        'grape sugar',
        'high-fructose corn syrup',
        'high-maltose corn syrup',
        'isomaltose',
        'isomaltulose',
        'lactose',
        'maltose',
        'maple sugar',
        'organic sugar',
        'palm sugar',
        'pearl sugar',
        'sanding sugar',
        'panocha',
        'raw sugar',
        'saccharose',
        'sucrose',
        'soft sugar',
        'sucrose',
        'sugar',
        'superfine sugar',
        'table sugar',
        'turbinado sugar',
        'white sugar'],

    'Sweetening Agents': [
        'syrup',
        'agave syrup',
        'apple cider syrup',
        'apple syrup',
        'brown rice syrup',
        'brown sugar',
        'yellow sugar',
        'golden sugar',
        'carob syrup',
        'concentrated maple water',
        'corn sweetener',
        'corn syrup',
        'corn syrup solids',
        'dextrose anhydrous',
        'dextrose monohydrate',
        'fancy molasses',
        'glucose',
        'glucose syrup',
        'glucose solid',
        'dried glucose syrup',
        'golden syrup',
        'honey',
        'icing sugar',
        "confectioner's sugar",
        'powdered sugar',
        'invert sugar',
        'liquid invert sugar',
        'liquid sugar',
        'malt syrup',
        'malted barley extract',
        'malted barley syrup',
        'maple syrup',
        'maple water',
        'oat syrup solids',
        'other syrups',
        'potato syrup solids',
        'raisin syrup',
        'refined sugar syrup',
        "refiners' syrup",
        'golden syrup',
        "refiners' molasses",
        'blackstrap molasses',
        'cooking molasses',
        'rice syrup',
        'sorghum syrup',
        'sweet sorghum',
        'table molasses',
        'tapioca syrup',
        'tapioca syrup solids',
        'wheat syrup'],
    'Sweetening Agent Substitute': [
        'condensed milk',
        'sweetened condensed milk',
        'decharacterized juice',
        'fruit juice',
        'fruit juice concentrate',
        'fruit paste',
        'fruit purée',
        'fruit purée concentrate',
        'malted milk',
        'malted milk powder',
        'maltodextrin',
        'nectar'],
    'Sweeteners': [
        'advantame',
        'acesulfame potassium',
        'aspartame',
        'calcium saccharin',
        'erythritol',
        'hydrogenated starch hydrolysates  ',
        'isomalt',
        'lactitol',
        'maltitol',
        'maltitol syrup',
        'mannitol',
        'monk fruit extract',
        'neotame',
        'potassium saccharin',
        'sorbitol',
        'saccharin',
        'sodium saccharin',
        'sorbitol syrup',
        'steviol glycosides',
        'sucralose',
        'thaumatin',
        'xylitol']
}

# regex built from the FREE_SUGARS list
FREE_SUGARS_REGEX = ".*barbados sugar.*|.*muscovado.*|.*barley malt.*|.*beet sugar.*|.*burnt sugar" \
                  ".*|.*caramelized sugar.*|.*cane juice.*|.*cane juice crystals.*|.*cane sugar.*|.*castor sugar" \
                  ".*|.*caster sugar.*|.*coarse sugar.*|.*coconut palm sugar.*|.*coconut sugar" \
                  ".*|.*crystalline fructose.*|.*date sugar.*|.*dehydrated cane juice.*|.*demerara-style sugar" \
                  ".*|.*evaporated cane juice.*|.*evaporated cane sugar.*|.*dried cane syrup.*|.*cane syrup solids" \
                  ".*|.*fondant sugar.*|.*free-flowing brown sugars.*|.*fructose.*|.*fructose solids" \
                  ".*|.*fructose syrup.*|.*fruit sugar.*|.*galactose.*|.*glucose-fructose.*|.*granulated sugar" \
                  ".*|.*grape sugar.*|.*high-fructose corn syrup.*|.*high-maltose corn syrup.*|.*isomaltose" \
                  ".*|.*isomaltulose.*|.*lactose.*|.*maltose.*|.*maple sugar.*|.*organic sugar.*|.*palm sugar" \
                  ".*|.*pearl sugar.*|.*sanding sugar.*|.*panocha.*|.*raw sugar.*|.*saccharose.*|.*sucrose" \
                  ".*|.*soft sugar.*|.*sucrose.*|.*sugar.*|.*superfine sugar.*|.*table sugar.*|.*turbinado sugar" \
                  ".*|.*white sugar.*|.*syrup.*|.*agave syrup.*|.*apple cider syrup.*|.*apple syrup" \
                  ".*|.*brown rice syrup.*|.*brown sugar.*|.*yellow sugar.*|.*golden sugar.*|.*carob syrup" \
                  ".*|.*concentrated maple water.*|.*corn sweetener.*|.*corn syrup.*|.*corn syrup solids" \
                  ".*|.*dextrose anhydrous.*|.*dextrose monohydrate.*|.*fancy molasses.*|.*glucose.*|.*glucose syrup" \
                  ".*|.*glucose solid.*|.*dried glucose syrup.*|.*golden syrup.*|.*honey.*|.*icing sugar" \
                  ".*|.*confectioner's sugar.*|.*powdered sugar.*|.*invert sugar.*|.*liquid invert sugar" \
                  ".*|.*liquid sugar.*|.*malt syrup.*|.*malted barley extract.*|.*malted barley syrup" \
                  ".*|.*maple syrup.*|.*maple water.*|.*oat syrup solids.*|.*other syrups.*|.*potato syrup solids" \
                  ".*|.*raisin syrup.*|.*refined sugar syrup.*|.*refiners' syrup.*|.*golden syrup" \
                  ".*|.*refiners' molasses.*|.*blackstrap molasses.*|.*cooking molasses.*|.*rice syrup" \
                  ".*|.*sorghum syrup.*|.*sweet sorghum.*|.*table molasses.*|.*tapioca syrup.*|.*tapioca syrup solids" \
                  ".*|.*wheat syrup.*|.*condensed milk.*|.*sweetened condensed milk.*|.*decharacterized juice" \
                  ".*|.*fruit juice.*|.*fruit juice concentrate.*|.*fruit paste.*|.*fruit purée" \
                  ".*|.*fruit purée concentrate.*|.*malted milk.*|.*malted milk powder.*|.*maltodextrin.*|.*nectar" \
                  ".*|.*advantame.*|.*acesulfame potassium.*|.*aspartame.*|.*calcium saccharin.*|.*erythritol" \
                  ".*|.*hydrogenated starch hydrolysates  .*|.*isomalt.*|.*lactitol.*|.*maltitol.*|.*maltitol syrup" \
                  ".*|.*mannitol.*|.*monk fruit extract.*|.*neotame.*|.*potassium saccharin.*|.*sorbitol" \
                  ".*|.*saccharin.*|.*sodium saccharin.*|.*sorbitol syrup.*|.*steviol glycosides.*|.*sucralose" \
                  ".*|.*thaumatin.*|.*xylitol.*"
