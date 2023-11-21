FROM pulumi/pulumi-python:latest as builder
FROM public.ecr.aws/lambda/python:3.11

COPY --from=builder /pulumi/bin/pulumi /pulumi/bin/pulumi
COPY --from=builder /pulumi/bin/*-python* /pulumi/bin

# Copy requirements.txt
COPY requirements.txt ${LAMBDA_TASK_ROOT}

# Install the specified packages
RUN pip install -r requirements.txt

# Copy function code
COPY lambda_function.py ${LAMBDA_TASK_ROOT}

ENV PATH "/pulumi/bin:${PATH}"
ENV PULUMI_ACCESS_TOKEN ""
# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
CMD [ "lambda_function.handler" ]