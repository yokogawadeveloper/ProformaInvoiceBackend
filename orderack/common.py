from .models import orderAcknowledgement


def generate_pi_no():
    global pi_code
    
    last_class_instance = orderAcknowledgement.objects.last()
    pi_code = '%d' % (last_class_instance.PI_NO + 1) if last_class_instance is not None else 1
    return int(pi_code)

